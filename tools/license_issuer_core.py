"""Shared offline license issuing helpers for the seller tools."""
from __future__ import annotations

import base64
import json
import os
import secrets
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

SUPPORTED_PLANS = {
    "personal_monthly": "个人版·月卡",
    "personal_launch": "个人版·首发年卡",
    "personal_annual": "个人版·常规年卡",
    "professional_annual": "专业版·年卡（后续开放）",
}

PLAN_DEFAULT_DAYS = {
    "personal_monthly": 30,
    "personal_launch": 365,
    "personal_annual": 365,
    "professional_annual": 365,
}


def default_days_for_plan(plan: str) -> int:
    try:
        return PLAN_DEFAULT_DAYS[plan]
    except KeyError as exc:
        raise ValueError("不支持的授权套餐") from exc


def encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def load_private_key(path: str | None = None) -> Ed25519PrivateKey:
    raw = os.getenv("LICENSE_PRIVATE_KEY", "").strip()
    if path:
        raw = Path(path).read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("请先选择 license-keys/private.key，或配置 LICENSE_PRIVATE_KEY")
    try:
        return Ed25519PrivateKey.from_private_bytes(
            base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
        )
    except (ValueError, TypeError) as exc:
        raise ValueError("私钥必须是 base64 编码的 32 字节 Ed25519 私钥") from exc


def issue_license(
    *,
    device_hash: str,
    plan: str,
    days: int,
    version: str,
    private_key_path: str | None = None,
    now: int | None = None,
) -> tuple[str, dict[str, Any]]:
    device_hash = device_hash.strip().lower()
    if len(device_hash) != 32 or any(char not in "0123456789abcdef" for char in device_hash):
        raise ValueError("设备指纹应为 32 位十六进制字符串")
    if plan not in SUPPORTED_PLANS:
        raise ValueError("不支持的授权套餐")
    if days <= 0 or days > 3660:
        raise ValueError("有效期必须在 1 到 3660 天之间")
    if not version.strip():
        raise ValueError("版本号不能为空")

    issued_at = int(time.time() if now is None else now)
    payload = {
        "license_id": secrets.token_hex(8),
        "plan": plan,
        "issued_at": issued_at,
        "expires_at": issued_at + days * 86400,
        "device_hash": device_hash,
        "version": version.strip(),
    }
    payload_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    code = f"YTR1.{encode(payload_bytes)}.{encode(load_private_key(private_key_path).sign(payload_bytes))}"
    return code, payload


def format_timestamp(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
