from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import auth
import src.app as app_module
from src.app import WebAuthMiddleware
from src.services import web_auth_service


def _fake_settings():
    return SimpleNamespace(
        web_username="admin",
        web_password="strong-password",
        web_session_secret="test-session-secret",
    )


def test_signed_session_round_trip_and_expiration(monkeypatch, tmp_path):
    monkeypatch.setattr(web_auth_service, "get_settings", _fake_settings)
    monkeypatch.setattr(web_auth_service, "WEB_AUTH_FILE", tmp_path / "web_auth.json")

    token = web_auth_service.create_session("admin", now=100)

    assert web_auth_service.authenticate_credentials("admin", "strong-password")
    assert not web_auth_service.authenticate_credentials("admin", "wrong")
    assert web_auth_service.get_session_username(token, now=100) == "admin"
    assert web_auth_service.get_session_username(token, now=100 + web_auth_service.SESSION_TTL_SECONDS) is None

    payload, signature = token.split(".", 1)
    tampered = f"{payload[:-1]}x.{signature}"
    assert web_auth_service.get_session_username(tampered, now=100) is None


def test_auth_routes_set_and_clear_http_only_cookie(monkeypatch, tmp_path):
    monkeypatch.setattr(web_auth_service, "get_settings", _fake_settings)
    monkeypatch.setattr(web_auth_service, "WEB_AUTH_FILE", tmp_path / "web_auth.json")

    app = FastAPI()
    app.include_router(auth.router)
    client = TestClient(app)

    unauthenticated = client.get("/auth/me")
    assert unauthenticated.status_code == 401

    login = client.post(
        "/auth/status",
        json={"username": "admin", "password": "strong-password"},
    )
    assert login.status_code == 200
    assert "httponly" in login.headers["set-cookie"].lower()
    assert login.json()["recovery_code"] is not None
    assert client.get("/auth/me").json() == {"authenticated": True, "username": "admin"}

    logout = client.post("/auth/logout")
    assert logout.status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_auth_routes_rate_limit_invalid_credentials(monkeypatch, tmp_path):
    monkeypatch.setattr(web_auth_service, "get_settings", _fake_settings)
    monkeypatch.setattr(auth, "get_settings", lambda: SimpleNamespace(
        web_cookie_secure=False,
        web_auth_max_attempts=2,
        web_auth_window_seconds=60,
        web_auth_lockout_seconds=60,
    ))
    monkeypatch.setattr(web_auth_service, "WEB_AUTH_FILE", tmp_path / "web_auth.json")
    auth._AUTH_FAILURES.clear()

    app = FastAPI()
    app.include_router(auth.router)
    client = TestClient(app)

    for _ in range(2):
        response = client.post("/auth/status", json={"username": "admin", "password": "wrong"})
        assert response.status_code == 401
    limited = client.post("/auth/status", json={"username": "admin", "password": "wrong"})
    assert limited.status_code == 429


def test_auth_routes_can_mark_session_cookie_secure(monkeypatch, tmp_path):
    monkeypatch.setattr(web_auth_service, "get_settings", _fake_settings)
    monkeypatch.setattr(auth, "get_settings", lambda: SimpleNamespace(web_cookie_secure=True))
    monkeypatch.setattr(web_auth_service, "WEB_AUTH_FILE", tmp_path / "web_auth.json")
    auth._AUTH_FAILURES.clear()

    app = FastAPI()
    app.include_router(auth.router)
    client = TestClient(app)
    response = client.post("/auth/status", json={"username": "admin", "password": "strong-password"})
    assert response.status_code == 200
    assert "secure" in response.headers["set-cookie"].lower()


def test_legacy_login_migrates_and_returns_a_recovery_code(monkeypatch, tmp_path):
    monkeypatch.setattr(web_auth_service, "get_settings", _fake_settings)
    monkeypatch.setattr(web_auth_service, "WEB_AUTH_FILE", tmp_path / "web_auth.json")

    app = FastAPI()
    app.include_router(auth.router)
    client = TestClient(app)

    login = client.post("/auth/status", json={"username": "admin", "password": "strong-password"})
    assert login.status_code == 200
    payload = login.json()
    assert payload["migrated"] is True
    assert payload["recovery_code"]

    client.post("/auth/logout")
    recovered = client.post("/auth/recover", json={
        "username": "admin",
        "recovery_code": payload["recovery_code"],
        "new_password": "recovered-password",
        "confirm_password": "recovered-password",
    })
    assert recovered.status_code == 200


def test_api_requests_are_rejected_without_a_valid_session(monkeypatch, tmp_path):
    monkeypatch.setattr(web_auth_service, "get_settings", _fake_settings)
    monkeypatch.setattr(web_auth_service, "WEB_AUTH_FILE", tmp_path / "web_auth.json")

    app = FastAPI()
    app.add_middleware(WebAuthMiddleware)
    app.include_router(auth.router)

    @app.get("/api/private")
    async def private_endpoint():
        return {"ok": True}

    client = TestClient(app)
    assert client.get("/api/private").status_code == 401

    login = client.post(
        "/auth/status",
        json={"username": "admin", "password": "strong-password"},
    )
    assert login.status_code == 200
    assert client.get("/api/private").json() == {"ok": True}


def test_expired_license_blocks_core_api_but_keeps_self_service_routes_open(monkeypatch, tmp_path):
    monkeypatch.setattr(web_auth_service, "get_settings", _fake_settings)
    monkeypatch.setattr(web_auth_service, "WEB_AUTH_FILE", tmp_path / "web_auth.json")
    monkeypatch.setattr(
        app_module,
        "get_license_status",
        lambda: SimpleNamespace(
            entitled=False,
            state="expired",
            code="TRIAL_EXPIRED",
            message="7 天试用已结束，请输入正式授权码",
        ),
    )

    app = FastAPI()
    app.add_middleware(WebAuthMiddleware)
    app.include_router(auth.router)

    @app.get("/api/private")
    async def private_endpoint():
        return {"ok": True}

    @app.get("/api/settings/pricing")
    async def pricing_endpoint():
        return {"ok": True}

    client = TestClient(app)
    login = client.post(
        "/auth/status",
        json={"username": "admin", "password": "strong-password"},
    )
    assert login.status_code == 200
    assert client.get("/api/private").status_code == 402
    assert client.get("/api/settings/pricing").json() == {"ok": True}


def test_register_change_and_recover_password(monkeypatch, tmp_path):
    monkeypatch.setattr(web_auth_service, "get_settings", lambda: SimpleNamespace(
        web_username="admin",
        web_password="admin123",
        web_session_secret="test-session-secret",
    ))
    monkeypatch.setattr(web_auth_service, "WEB_AUTH_FILE", tmp_path / "web_auth.json")

    recovery_code = web_auth_service.register_account("owner", "first-password")
    assert web_auth_service.is_registration_required() is False
    assert web_auth_service.authenticate_credentials("owner", "first-password")
    assert "first-password" not in (tmp_path / "web_auth.json").read_text(encoding="utf-8")

    web_auth_service.change_password("owner", "first-password", "second-password")
    assert not web_auth_service.authenticate_credentials("owner", "first-password")
    assert web_auth_service.authenticate_credentials("owner", "second-password")

    web_auth_service.recover_password("owner", recovery_code, "recovered-password")
    assert web_auth_service.authenticate_credentials("owner", "recovered-password")
    assert not web_auth_service.authenticate_credentials("owner", "second-password")

    try:
        web_auth_service.recover_password("owner", recovery_code, "another-password")
    except PermissionError:
        pass
    else:
        raise AssertionError("recovery codes must be single-use")


def test_custom_legacy_env_account_cannot_be_overwritten_by_registration(monkeypatch, tmp_path):
    monkeypatch.setattr(web_auth_service, "get_settings", _fake_settings)
    monkeypatch.setattr(web_auth_service, "WEB_AUTH_FILE", tmp_path / "web_auth.json")

    assert web_auth_service.is_registration_available() is False
    assert web_auth_service.is_registration_required() is False
    try:
        web_auth_service.register_account("attacker", "safe-password")
    except FileExistsError:
        pass
    else:
        raise AssertionError("custom legacy credentials must not be overwritten")


def test_auth_routes_support_registration_password_change_and_recovery(monkeypatch, tmp_path):
    monkeypatch.setattr(web_auth_service, "get_settings", lambda: SimpleNamespace(
        web_username="admin",
        web_password="admin123",
        web_session_secret="test-session-secret",
    ))
    monkeypatch.setattr(web_auth_service, "WEB_AUTH_FILE", tmp_path / "web_auth.json")

    app = FastAPI()
    app.include_router(auth.router)
    client = TestClient(app)

    setup = client.get("/auth/setup")
    assert setup.json()["registration_required"] is True

    register = client.post("/auth/register", json={
        "username": "owner",
        "password": "first-password",
        "confirm_password": "first-password",
    })
    assert register.status_code == 200
    recovery_code = register.json()["recovery_code"]
    assert client.get("/auth/me").json()["username"] == "owner"

    changed = client.post("/auth/password", json={
        "current_password": "first-password",
        "new_password": "second-password",
        "confirm_password": "second-password",
    })
    assert changed.status_code == 200
    client.post("/auth/logout")

    recovered = client.post("/auth/recover", json={
        "username": "owner",
        "recovery_code": recovery_code,
        "new_password": "recovered-password",
        "confirm_password": "recovered-password",
    })
    assert recovered.status_code == 200
    assert client.get("/auth/me").json()["username"] == "owner"
