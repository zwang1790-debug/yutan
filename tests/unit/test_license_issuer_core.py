import base64

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.services import license_service
from tools.license_issuer_core import default_days_for_plan, issue_license


def _write_private_key(tmp_path):
    private_key = Ed25519PrivateKey.generate()
    raw_private_key = private_key.private_bytes(
        serialization.Encoding.Raw,
        serialization.PrivateFormat.Raw,
        serialization.NoEncryption(),
    )
    key_path = tmp_path / "seller-private.key"
    key_path.write_text(base64.urlsafe_b64encode(raw_private_key).decode().rstrip("=") + "\n", encoding="ascii")
    return private_key, key_path


@pytest.mark.parametrize(
    ("plan", "expected_days"),
    [
        ("personal_monthly", 30),
        ("personal_launch", 365),
        ("personal_annual", 365),
        ("professional_annual", 365),
    ],
)
def test_default_days_match_plan_billing_period(plan, expected_days):
    assert default_days_for_plan(plan) == expected_days


def test_default_days_rejects_unknown_plan():
    with pytest.raises(ValueError, match="不支持"):
        default_days_for_plan("unknown")


def test_issue_license_creates_client_verifiable_bound_license(monkeypatch, tmp_path):
    private_key, key_path = _write_private_key(tmp_path)
    public_key = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    monkeypatch.setenv("LICENSE_PUBLIC_KEY", base64.urlsafe_b64encode(public_key).decode().rstrip("="))
    monkeypatch.setattr(license_service, "LICENSE_STATE_PATH", tmp_path / "license-state.json")
    monkeypatch.delenv("LICENSE_STATE_FILE", raising=False)
    device_hash = license_service.get_device_hash()

    code, payload = issue_license(
        device_hash=device_hash,
        plan="personal_annual",
        days=365,
        version="2.1.1",
        private_key_path=str(key_path),
        now=1_700_000_000,
    )

    assert code.startswith("YTR1.")
    assert payload["plan"] == "personal_annual"
    assert payload["device_hash"] == device_hash
    assert payload["expires_at"] == 1_700_000_000 + 365 * 86400
    assert license_service.activate_license(code, now=1_700_000_001).state == "licensed"


@pytest.mark.parametrize(
    ("device_hash", "plan", "days", "message"),
    [
        ("invalid", "personal_annual", 365, "设备指纹"),
        ("a" * 32, "monthly", 365, "不支持"),
        ("a" * 32, "personal_annual", 0, "有效期"),
        ("a" * 32, "personal_annual", 3661, "有效期"),
    ],
)
def test_issue_license_rejects_invalid_seller_input(tmp_path, device_hash, plan, days, message):
    _private_key, key_path = _write_private_key(tmp_path)

    with pytest.raises(ValueError, match=message):
        issue_license(
            device_hash=device_hash,
            plan=plan,
            days=days,
            version="2.1.1",
            private_key_path=str(key_path),
            now=1_700_000_000,
        )
