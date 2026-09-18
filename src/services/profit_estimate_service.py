"""商品利润估算的持久化与计算服务。"""
from __future__ import annotations

from datetime import datetime
import math
from typing import Any, Iterable

from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.infrastructure.persistence.sqlite_connection import sqlite_connection


ESTIMATE_FIELDS = (
    "purchase_price",
    "resale_price",
    "platform_fee",
    "shipping_cost",
    "other_cost",
)


def _as_non_negative_number(value: Any, field: str) -> float:
    try:
        number = round(float(value), 2)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} 必须是数字。") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} 必须是有限数字。")
    if number < 0:
        raise ValueError(f"{field} 不能小于 0。")
    return number


def normalize_estimate(payload: dict[str, Any]) -> dict[str, float]:
    return {
        field: _as_non_negative_number(payload.get(field, 0), field)
        for field in ESTIMATE_FIELDS
    }


def calculate_profit(estimate: dict[str, Any]) -> dict[str, float]:
    values = normalize_estimate(estimate)
    profit = round(
        values["resale_price"]
        - values["purchase_price"]
        - values["platform_fee"]
        - values["shipping_cost"]
        - values["other_cost"],
        2,
    )
    revenue = values["resale_price"]
    return {
        **values,
        "profit": profit,
        "margin": round((profit / revenue) * 100, 2) if revenue else 0.0,
    }


def load_profit_estimates(
    result_filename: str, item_ids: Iterable[str] | None = None
) -> dict[str, dict[str, Any]]:
    bootstrap_sqlite_storage()
    params: list[Any] = [result_filename]
    condition = "result_filename = ?"
    normalized_ids = [
        str(item_id).strip()
        for item_id in (item_ids or [])
        if str(item_id).strip()
    ]
    if normalized_ids:
        placeholders = ", ".join("?" for _ in normalized_ids)
        condition += f" AND item_id IN ({placeholders})"
        params.extend(normalized_ids)

    with sqlite_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM profit_estimates WHERE {condition}", tuple(params)
        ).fetchall()
    return {
        str(row["item_id"]): {
            "purchase_price": row["purchase_price"],
            "resale_price": row["resale_price"],
            "platform_fee": row["platform_fee"],
            "shipping_cost": row["shipping_cost"],
            "other_cost": row["other_cost"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    }


def save_profit_estimate(
    result_filename: str, item_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    normalized_item_id = str(item_id or "").strip()
    if not normalized_item_id:
        raise ValueError("商品缺少商品 ID，无法保存利润估算。")
    values = normalize_estimate(payload)
    updated_at = datetime.now().isoformat(timespec="seconds")
    bootstrap_sqlite_storage()
    with sqlite_connection() as conn:
        conn.execute(
            """
            INSERT INTO profit_estimates (
                result_filename, item_id, purchase_price, resale_price,
                platform_fee, shipping_cost, other_cost, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(result_filename, item_id) DO UPDATE SET
                purchase_price = excluded.purchase_price,
                resale_price = excluded.resale_price,
                platform_fee = excluded.platform_fee,
                shipping_cost = excluded.shipping_cost,
                other_cost = excluded.other_cost,
                updated_at = excluded.updated_at
            """,
            (
                result_filename,
                normalized_item_id,
                values["purchase_price"],
                values["resale_price"],
                values["platform_fee"],
                values["shipping_cost"],
                values["other_cost"],
                updated_at,
            ),
        )
        conn.commit()
    return {**values, "updated_at": updated_at}
