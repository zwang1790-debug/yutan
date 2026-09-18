import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import dependencies as deps
from src.api.routes import license
from src.services import license_service


class _TaskService:
    async def get_all_tasks(self):
        return []


class _Scheduler:
    def __init__(self):
        self.reload_calls = 0
        self.started = False

    async def reload_jobs(self, _tasks):
        self.reload_calls += 1

    def start(self):
        self.started = True


def _make_code(private_key, payload):
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    encode = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    return f"YTR1.{encode(raw)}.{encode(private_key.sign(raw))}"


def test_status_starts_trial_and_activation_reloads_scheduler(monkeypatch, tmp_path):
    monkeypatch.setattr(license_service, "LICENSE_STATE_PATH", tmp_path / "license.json")
    monkeypatch.delenv("LICENSE_STATE_FILE", raising=False)
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    monkeypatch.setenv("LICENSE_PUBLIC_KEY", base64.urlsafe_b64encode(public_key).decode().rstrip("="))

    scheduler = _Scheduler()
    app = FastAPI()
    app.include_router(license.router)
    app.dependency_overrides[deps.get_task_service] = _TaskService
    app.dependency_overrides[deps.get_scheduler_service] = lambda: scheduler
    client = TestClient(app)

    assert client.get("/api/license/status").json()["state"] == "trial"
    payload = {"license_id": "test", "plan": "annual", "issued_at": 1, "expires_at": 4_000_000_000, "device_hash": license_service.get_device_hash(), "version": "2.1.1"}
    response = client.post("/api/license/activate", json={"code": _make_code(private_key, payload)})
    assert response.status_code == 200
    assert response.json()["state"] == "licensed"
    assert scheduler.reload_calls == 1
    assert scheduler.started is True
