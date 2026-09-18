"""Authentication endpoints for the local web console."""
from __future__ import annotations

import threading
import time

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel

from src.infrastructure.config.settings import get_settings
from src.services.web_auth_service import (
    PASSWORD_MIN_LENGTH,
    SESSION_COOKIE_NAME,
    SESSION_TTL_SECONDS,
    authenticate_credentials,
    change_password,
    create_session,
    generate_recovery_code,
    get_session_username,
    is_registration_available,
    is_registration_required,
    migrate_legacy_account,
    recover_password,
    register_account,
    validate_password,
)


router = APIRouter(prefix="/auth", tags=["auth"])
_AUTH_FAILURES: dict[str, list[float]] = {}
_AUTH_LOCK = threading.Lock()


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    confirm_password: str


class PasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class RecoveryRequest(BaseModel):
    username: str
    recovery_code: str
    new_password: str
    confirm_password: str


class RecoveryCodeRequest(BaseModel):
    current_password: str


def _set_session_cookie(response: Response, username: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session(username),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=bool(getattr(settings, "web_cookie_secure", False)),
        path="/",
    )


def _auth_client_key(request: Request) -> str:
    client = request.client
    return client.host if client and client.host else "local"


def _prune_auth_failures(key: str, now: float) -> list[float]:
    settings = get_settings()
    window = int(getattr(settings, "web_auth_window_seconds", 900))
    failures = [stamp for stamp in _AUTH_FAILURES.get(key, []) if now - stamp < window]
    if failures:
        _AUTH_FAILURES[key] = failures
    else:
        _AUTH_FAILURES.pop(key, None)
    return failures


def _ensure_auth_not_locked(request: Request) -> None:
    key = _auth_client_key(request)
    now = time.monotonic()
    settings = get_settings()
    max_attempts = int(getattr(settings, "web_auth_max_attempts", 5))
    lockout = int(getattr(settings, "web_auth_lockout_seconds", 900))
    with _AUTH_LOCK:
        failures = _prune_auth_failures(key, now)
        if len(failures) >= max_attempts and now - failures[-1] < lockout:
            raise HTTPException(status_code=429, detail="登录尝试过于频繁，请稍后再试")


def _record_auth_failure(request: Request) -> None:
    key = _auth_client_key(request)
    now = time.monotonic()
    with _AUTH_LOCK:
        failures = _prune_auth_failures(key, now)
        failures.append(now)
        _AUTH_FAILURES[key] = failures


def _clear_auth_failures(request: Request) -> None:
    with _AUTH_LOCK:
        _AUTH_FAILURES.pop(_auth_client_key(request), None)


def _current_user(request: Request) -> str:
    username = get_session_username(request.cookies.get(SESSION_COOKIE_NAME))
    if not username:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return username


def _validate_password_pair(password: str, confirm_password: str) -> None:
    try:
        validate_password(password)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的密码不一致")


@router.get("/setup")
async def auth_setup():
    return {
        "registration_required": is_registration_required(),
        "registration_available": is_registration_available(),
        "password_min_length": PASSWORD_MIN_LENGTH,
    }


@router.post("/register")
async def auth_register(payload: RegisterRequest, response: Response):
    _validate_password_pair(payload.password, payload.confirm_password)
    try:
        recovery_code = register_account(payload.username, payload.password)
    except FileExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    _set_session_cookie(response, payload.username.strip())
    return {
        "authenticated": True,
        "username": payload.username.strip(),
        "recovery_code": recovery_code,
    }


@router.post("/status")
async def auth_status(payload: LoginRequest, response: Response, request: Request):
    """Validate credentials and establish a signed HttpOnly session cookie."""
    if is_registration_required():
        raise HTTPException(status_code=409, detail="请先注册管理员账号")
    _ensure_auth_not_locked(request)
    if not authenticate_credentials(payload.username, payload.password):
        _record_auth_failure(request)
        raise HTTPException(status_code=401, detail="认证失败")

    _clear_auth_failures(request)
    username = payload.username.strip()
    migrated_recovery_code = migrate_legacy_account(username, payload.password)
    _set_session_cookie(response, username)
    return {
        "authenticated": True,
        "username": username,
        "migrated": migrated_recovery_code is not None,
        "recovery_code": migrated_recovery_code,
    }


@router.get("/me")
async def auth_me(request: Request):
    username = _current_user(request)
    return {"authenticated": True, "username": username}


@router.post("/logout")
async def auth_logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")
    return {"authenticated": False}


@router.post("/password")
async def auth_change_password(payload: PasswordRequest, request: Request, response: Response):
    username = _current_user(request)
    _validate_password_pair(payload.new_password, payload.confirm_password)
    try:
        change_password(username, payload.current_password, payload.new_password)
    except PermissionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    _set_session_cookie(response, username)
    return {"authenticated": True, "username": username}


@router.post("/recovery-code")
async def auth_generate_recovery_code(payload: RecoveryCodeRequest, request: Request):
    username = _current_user(request)
    try:
        recovery_code = generate_recovery_code(username, payload.current_password)
    except PermissionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"username": username, "recovery_code": recovery_code}


@router.post("/recover")
async def auth_recover_password(payload: RecoveryRequest, response: Response, request: Request):
    _validate_password_pair(payload.new_password, payload.confirm_password)
    _ensure_auth_not_locked(request)
    try:
        recover_password(payload.username.strip(), payload.recovery_code, payload.new_password)
    except PermissionError as error:
        _record_auth_failure(request)
        raise HTTPException(status_code=400, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    _clear_auth_failures(request)
    username = payload.username.strip()
    _set_session_cookie(response, username)
    return {"authenticated": True, "username": username}
