import base64
import json

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.services import license_service


def _code(private_key, payload):
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    enc = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    return f"YTR1.{enc(raw)}.{enc(private_key.sign(raw))}"


def test_trial_starts_once_and_expires(monkeypatch, tmp_path):
    monkeypatch.setattr(license_service, "LICENSE_STATE_PATH", tmp_path / "license.json")
    monkeypatch.delenv("LICENSE_STATE_FILE", raising=False)
    first = license_service.get_license_status(now=1000)
    assert first.state == "trial"
    assert first.trial_expires_at == 1000 + 7 * 86400
    expired = license_service.get_license_status(now=1000 + 7 * 86400)
    assert expired.code == "TRIAL_EXPIRED"


def test_signed_license_binds_device_and_rejects_tampering(monkeypatch, tmp_path):
    monkeypatch.setattr(license_service, "LICENSE_STATE_PATH", tmp_path / "license.json")
    monkeypatch.delenv("LICENSE_STATE_FILE", raising=False)
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    monkeypatch.setenv("LICENSE_PUBLIC_KEY", base64.urlsafe_b64encode(public_key).decode().rstrip("="))
    device_hash = license_service.get_device_hash()
    payload = {"license_id": "demo", "plan": "monthly", "issued_at": 1000, "expires_at": 5000, "device_hash": device_hash, "version": "2.1.1"}
    status = license_service.activate_license(_code(private_key, payload), now=2000)
    assert status.state == "licensed"
    assert status.plan == "monthly"

    raw = json.dumps(payload | {"plan": "annual"}, separators=(",", ":"), sort_keys=True).encode()
    enc = lambda value: base64.urlsafe_b64encode(value).decode().rstrip("=")
    tampered = f"YTR1.{enc(raw)}.{enc(private_key.sign(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()))}"
    try:
        license_service.activate_license(tampered, now=2000)
    except license_service.LicenseError as exc:
        assert exc.code == "INVALID_LICENSE"
    else:
        raise AssertionError("tampered license must be rejected")


def test_license_rejects_other_device(monkeypatch, tmp_path):
    monkeypatch.setattr(license_service, "LICENSE_STATE_PATH", tmp_path / "license.json")
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    monkeypatch.setenv("LICENSE_PUBLIC_KEY", base64.urlsafe_b64encode(public_key).decode().rstrip("="))
    payload = {"license_id": "demo", "plan": "monthly", "issued_at": 1000, "expires_at": 5000, "device_hash": "other-device", "version": "2.1.1"}
    try:
        license_service.activate_license(_code(private_key, payload), now=2000)
    except license_service.LicenseError as exc:
        assert exc.code == "DEVICE_MISMATCH"
    else:
        raise AssertionError("other device must be rejected")


def test_frozen_build_ignores_environment_public_key(monkeypatch):
    monkeypatch.setattr(license_service.sys, "frozen", True, raising=False)
    monkeypatch.setenv("LICENSE_PUBLIC_KEY", "not-the-seller-key")

    public_key = license_service._public_key()

    assert public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
