"""Local administrator account and signed session support for the web console.

The console is a local application, so the account record intentionally lives
next to the existing application data. Passwords and recovery codes are never
stored in plaintext. The legacy WEB_USERNAME/WEB_PASSWORD pair remains
supported long enough to migrate an existing installation on first login.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from typing import Any

from src.infrastructure.config.settings import get_settings


SESSION_COOKIE_NAME = "fish_radar_session"
SESSION_TTL_SECONDS = 60 * 60 * 12
PASSWORD_MIN_LENGTH = 8
PBKDF2_ITERATIONS = 310_000
WEB_AUTH_FILE = Path(os.getenv("WEB_AUTH_FILE", "data/web_auth.json"))
LEGACY_DEFAULT_USERNAME = "admin"
LEGACY_DEFAULT_PASSWORD = "admin123"


def _auth_file_path() -> Path:
    configured = os.getenv("WEB_AUTH_FILE")
    if configured:
        return Path(configured)
    configured = getattr(get_settings(), "web_auth_file", "")
    return Path(configured) if configured else Path(WEB_AUTH_FILE)


def _settings_value(name: str, default: str = "") -> str:
    value = getattr(get_settings(), name, default)
    return str(value or "")


def _read_account() -> dict[str, Any] | None:
    path = _auth_file_path()
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return payload if isinstance(payload, dict) and payload.get("username") else None


def _write_account(account: dict[str, Any]) -> None:
    path = _auth_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(account, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    os.replace(temporary, path)


def _encoded_digest(value: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        value.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return base64.urlsafe_b64encode(digest).decode("ascii")


def _new_digest(value: str) -> tuple[str, str]:
    salt = secrets.token_bytes(16)
    return (
        base64.urlsafe_b64encode(salt).decode("ascii"),
        _encoded_digest(value, salt),
    )


def _matches_digest(value: str, salt_value: str, expected: str) -> bool:
    try:
        salt = base64.urlsafe_b64decode(salt_value.encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        return False
    actual = _encoded_digest(value, salt)
    return hmac.compare_digest(actual, expected)


def _validate_username(username: str) -> str:
    normalized = username.strip()
    if not normalized or len(normalized) > 64 or any(char.isspace() for char in normalized):
        raise ValueError("用户名不能为空，且不能包含空格")
    return normalized


def validate_password(password: str) -> str:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise ValueError(f"密码长度不能少于 {PASSWORD_MIN_LENGTH} 位")
    return password


def _legacy_account_is_configured() -> bool:
    """Return whether an existing installation explicitly configured credentials."""
    username = _settings_value("web_username")
    password = _settings_value("web_password")
    if not username or not password:
        return False
    return (username, password) != (LEGACY_DEFAULT_USERNAME, LEGACY_DEFAULT_PASSWORD)


def is_registration_available() -> bool:
    return _read_account() is None and not _legacy_account_is_configured()


def is_registration_required() -> bool:
    return is_registration_available()


def get_account_username() -> str | None:
    account = _read_account()
    if account:
        return str(account["username"])
    if _legacy_account_is_configured():
        return _settings_value("web_username")
    return None


def register_account(username: str, password: str) -> str:
    if not is_registration_available():
        raise FileExistsError("管理员账号已经存在，或已配置旧版 .env 账号")
    username = _validate_username(username)
    password = validate_password(password)
    password_salt, password_hash = _new_digest(password)
    recovery_code = _new_recovery_code()
    recovery_salt, recovery_hash = _new_digest(recovery_code)
    now = int(time.time())
    _write_account(
        {
            "version": 1,
            "username": username,
            "salt": password_salt,
            "password_hash": password_hash,
            "recovery_code_salt": recovery_salt,
            "recovery_code_hash": recovery_hash,
            "created_at": now,
            "updated_at": now,
        }
    )
    return recovery_code


def authenticate_credentials(username: str, password: str) -> bool:
    username = username.strip()
    account = _read_account()
    if account:
        return hmac.compare_digest(username, str(account.get("username", ""))) and _matches_digest(
            password,
            str(account.get("salt", "")),
            str(account.get("password_hash", "")),
        )
    if not _legacy_account_is_configured():
        return False
    return hmac.compare_digest(username, _settings_value("web_username")) and hmac.compare_digest(
        password, _settings_value("web_password")
    )


def migrate_legacy_account(username: str, password: str) -> str | None:
    if _read_account() or not authenticate_credentials(username, password):
        return None
    if not _legacy_account_is_configured():
        return None
    username = _validate_username(username)
    password_salt, password_hash = _new_digest(password)
    recovery_code = _new_recovery_code()
    recovery_salt, recovery_hash = _new_digest(recovery_code)
    now = int(time.time())
    _write_account(
        {
            "version": 1,
            "username": username,
            "salt": password_salt,
            "password_hash": password_hash,
            "recovery_code_salt": recovery_salt,
            "recovery_code_hash": recovery_hash,
            "created_at": now,
            "updated_at": now,
        }
    )
    return recovery_code


def _new_recovery_code() -> str:
    raw = secrets.token_hex(6).upper()
    return f"{raw[:4]}-{raw[4:8]}-{raw[8:]}"


def _require_account(username: str) -> dict[str, Any]:
    account = _read_account()
    if not account or not hmac.compare_digest(str(account.get("username", "")), username):
        raise ValueError("账号不存在")
    return account


def change_password(username: str, current_password: str, new_password: str) -> None:
    account = _require_account(username)
    if not _matches_digest(current_password, str(account.get("salt", "")), str(account.get("password_hash", ""))):
        raise PermissionError("当前密码错误")
    new_password = validate_password(new_password)
    salt, password_hash = _new_digest(new_password)
    account.update({"salt": salt, "password_hash": password_hash, "updated_at": int(time.time())})
    _write_account(account)


def generate_recovery_code(username: str, current_password: str) -> str:
    account = _require_account(username)
    if not _matches_digest(current_password, str(account.get("salt", "")), str(account.get("password_hash", ""))):
        raise PermissionError("当前密码错误")
    recovery_code = _new_recovery_code()
    salt, recovery_hash = _new_digest(recovery_code)
    account.update(
        {
            "recovery_code_salt": salt,
            "recovery_code_hash": recovery_hash,
            "updated_at": int(time.time()),
        }
    )
    _write_account(account)
    return recovery_code


def recover_password(username: str, recovery_code: str, new_password: str) -> None:
    account = _require_account(username)
    if not _matches_digest(
        recovery_code.strip().upper(),
        str(account.get("recovery_code_salt", "")),
        str(account.get("recovery_code_hash", "")),
    ):
        raise PermissionError("恢复码无效或已失效")
    new_password = validate_password(new_password)
    salt, password_hash = _new_digest(new_password)
    account.update(
        {
            "salt": salt,
            "password_hash": password_hash,
            "recovery_code_salt": "",
            "recovery_code_hash": "",
            "updated_at": int(time.time()),
        }
    )
    _write_account(account)


def _session_secret(username: str) -> bytes:
    configured = _settings_value("web_session_secret")
    account = _read_account()
    if account and str(account.get("username")) == username:
        password_material = str(account.get("password_hash", ""))
    else:
        password_material = _settings_value("web_password")
    material = f"{configured}|{username}|{password_material}".encode("utf-8")
    return hashlib.sha256(material).digest()


def create_session(username: str, now: int | None = None) -> str:
    issued_at = int(time.time() if now is None else now)
    payload = f"{username}|{issued_at}".encode("utf-8")
    encoded = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(_session_secret(username), encoded.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded}.{signature}"


def get_session_username(token: str | None, now: int | None = None) -> str | None:
    if not token or "." not in token:
        return None
    encoded, signature = token.split(".", 1)
    try:
        payload = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)).decode("utf-8")
        username, issued_at_text = payload.rsplit("|", 1)
        issued_at = int(issued_at_text)
    except (ValueError, UnicodeDecodeError, base64.binascii.Error):
        return None
    expected = hmac.new(_session_secret(username), encoded.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    current_time = int(time.time() if now is None else now)
    if issued_at > current_time or current_time - issued_at >= SESSION_TTL_SECONDS:
        return None
    if not authenticate_session_username(username):
        return None
    return username


def authenticate_session_username(username: str) -> bool:
    account = _read_account()
    if account:
        return hmac.compare_digest(str(account.get("username", "")), username)
    return _legacy_account_is_configured() and hmac.compare_digest(
        username, _settings_value("web_username")
    )
