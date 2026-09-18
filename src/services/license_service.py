"""Local signed license and trial entitlement service.

The client only needs the public key. The private key belongs to the seller's
offline issuing tool and must never be bundled with the application.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import socket
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

TRIAL_DAYS = 7
LICENSE_PREFIX = "YTR1"
LICENSE_STATE_PATH = Path("data/license_state.json")
DEFAULT_PUBLIC_KEY = "WsbL_vSm2LyB7wkXz8VwbSiYDEYfoFvnInJ9r-5x5fI"


class LicenseError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class LicenseStatus:
    state: str
    code: str | None
    message: str
    trial_started_at: int | None
    trial_expires_at: int | None
    license_id: str | None
    plan: str | None
    issued_at: int | None
    expires_at: int | None
    device_hash: str
    version: str | None
    clock_tampered: bool = False

    @property
    def entitled(self) -> bool:
        return self.state in {"trial", "licensed"}

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "code": self.code,
            "message": self.message,
            "entitled": self.entitled,
            "trial_started_at": self.trial_started_at,
            "trial_expires_at": self.trial_expires_at,
            "license_id": self.license_id,
            "plan": self.plan,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "device_hash": self.device_hash,
            "version": self.version,
            "clock_tampered": self.clock_tampered,
        }


def _state_path() -> Path:
    return Path(os.getenv("LICENSE_STATE_FILE", str(LICENSE_STATE_PATH)))


def _read_state() -> dict[str, Any]:
    try:
        payload = json.loads(_state_path().read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return {}


def _write_state(payload: dict[str, Any]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value.encode("ascii") + b"=" * (-len(value) % 4))


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def get_device_hash() -> str:
    """Return a stable, non-reversible device identifier for display/binding."""
    parts = [
        platform.system(), platform.machine(), platform.node(),
        str(uuid.getnode()), os.getenv("USERNAME") or os.getenv("USER") or "",
        socket.gethostname(),
    ]
    digest = hashlib.sha256("|".join(parts).encode("utf-8", "ignore")).hexdigest()
    return digest[:32]


def _public_key() -> Ed25519PublicKey:
    # Frozen customer builds must use the embedded seller key. Environment
    # overrides remain available in source mode for local development/tests.
    configured = os.getenv("LICENSE_PUBLIC_KEY", "").strip()
    raw = DEFAULT_PUBLIC_KEY if getattr(sys, "frozen", False) else (configured or DEFAULT_PUBLIC_KEY)
    if not raw:
        raise LicenseError("LICENSE_NOT_CONFIGURED", "当前版本尚未配置授权验证公钥")
    try:
        decoded = _b64decode(raw)
        return Ed25519PublicKey.from_public_bytes(decoded)
    except (ValueError, TypeError, UnicodeError) as exc:
        raise LicenseError("LICENSE_NOT_CONFIGURED", "授权验证公钥配置无效") from exc


def _verify_license(code: str) -> dict[str, Any]:
    parts = code.strip().split(".")
    if len(parts) != 3 or parts[0] != LICENSE_PREFIX:
        raise LicenseError("INVALID_LICENSE", "授权码格式无效")
    try:
        payload_bytes = _b64decode(parts[1])
        signature = _b64decode(parts[2])
        payload = json.loads(payload_bytes.decode("utf-8"))
        _public_key().verify(signature, payload_bytes)
    except (ValueError, TypeError, UnicodeError, json.JSONDecodeError, InvalidSignature) as exc:
        raise LicenseError("INVALID_LICENSE", "授权码签名无效或内容已被修改") from exc
    if not isinstance(payload, dict):
        raise LicenseError("INVALID_LICENSE", "授权码内容无效")
    required = {"license_id", "plan", "issued_at", "expires_at", "device_hash", "version"}
    if not required.issubset(payload):
        raise LicenseError("INVALID_LICENSE", "授权码缺少必要字段")
    return payload


def _status_from_state(state: dict[str, Any], now: int) -> LicenseStatus:
    device_hash = get_device_hash()
    last_seen = int(state.get("last_seen_at", 0) or 0)
    clock_tampered = last_seen > now + 300
    if clock_tampered:
        return LicenseStatus("blocked", "CLOCK_TAMPERED", "检测到系统时间异常，请校准后重启应用", None, None, None, None, None, None, device_hash, None, True)

    license_payload = state.get("license") if isinstance(state.get("license"), dict) else None
    if license_payload:
        expires_at = int(license_payload.get("expires_at", 0) or 0)
        if license_payload.get("device_hash") != device_hash:
            return LicenseStatus("blocked", "DEVICE_MISMATCH", "授权码未绑定当前设备", None, None, license_payload.get("license_id"), license_payload.get("plan"), license_payload.get("issued_at"), expires_at, device_hash, license_payload.get("version"))
        if expires_at <= now:
            return LicenseStatus("expired", "LICENSE_EXPIRED", "授权已到期，请输入新的授权码", None, None, license_payload.get("license_id"), license_payload.get("plan"), license_payload.get("issued_at"), expires_at, device_hash, license_payload.get("version"))
        return LicenseStatus("licensed", None, "正式授权有效", None, None, license_payload.get("license_id"), license_payload.get("plan"), license_payload.get("issued_at"), expires_at, device_hash, license_payload.get("version"))

    trial_started = int(state.get("trial_started_at", 0) or 0)
    if not trial_started:
        trial_started = now
        state["trial_started_at"] = trial_started
    trial_expires = trial_started + TRIAL_DAYS * 86400
    if trial_expires <= now:
        return LicenseStatus("expired", "TRIAL_EXPIRED", "7 天试用已结束，请输入正式授权码", trial_started, trial_expires, None, "trial", None, None, device_hash, None)
    return LicenseStatus("trial", None, "7 天试用有效", trial_started, trial_expires, None, "trial", None, None, device_hash, None)


def get_license_status(now: int | None = None) -> LicenseStatus:
    current = int(time.time() if now is None else now)
    state = _read_state()
    status = _status_from_state(state, current)
    state["last_seen_at"] = max(int(state.get("last_seen_at", 0) or 0), current)
    _write_state(state)
    return status


def activate_license(code: str, now: int | None = None) -> LicenseStatus:
    current = int(time.time() if now is None else now)
    payload = _verify_license(code)
    if payload["device_hash"] != get_device_hash():
        raise LicenseError("DEVICE_MISMATCH", "授权码不是为当前设备签发")
    if int(payload["expires_at"]) <= current:
        raise LicenseError("LICENSE_EXPIRED", "授权码已经过期")
    state = _read_state()
    state["license"] = payload
    state["last_seen_at"] = max(int(state.get("last_seen_at", 0) or 0), current)
    _write_state(state)
    return get_license_status(current)
