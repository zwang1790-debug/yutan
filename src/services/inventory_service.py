"""经营台账的持久化与实际利润计算。"""
from __future__ import annotations

from datetime import datetime
import math
from typing import Any, Iterable

from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.infrastructure.persistence.sqlite_connection import sqlite_connection


INVENTORY_STATUSES = {
    "discovered",
    "contacting",
    "purchased",
    "listed",
    "sold",
    "skipped",
}
OPTIONAL_AMOUNT_FIELDS = ("actual_purchase_price", "actual_sale_price")
COST_FIELDS = (
    "actual_platform_fee",
    "actual_shipping_cost",
    "actual_other_cost",
)


def _as_amount(value: Any, field: str, *, allow_none: bool) -> float | None:
    if value is None and allow_none:
        return None
    try:
        number = round(float(value), 2)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} 必须是数字。") from exc
    if not math.isfinite(number):
        raise ValueError(f"{field} 必须是有限数字。")
    if number < 0:
        raise ValueError(f"{field} 不能小于 0。")
    return number


def _normalize_status(value: Any) -> str:
    status = str(value or "").strip()
    if status not in INVENTORY_STATUSES:
        raise ValueError("台账状态不受支持。")
    return status


def calculate_actual_profit(record: dict[str, Any]) -> dict[str, Any]:
    purchase_price = record.get("actual_purchase_price")
    sale_price = record.get("actual_sale_price")
    if purchase_price is None or sale_price is None:
        return {**record, "actual_profit": None, "actual_margin": None}

    profit = round(
        float(sale_price)
        - float(purchase_price)
        - float(record.get("actual_platform_fee") or 0)
        - float(record.get("actual_shipping_cost") or 0)
        - float(record.get("actual_other_cost") or 0),
        2,
    )
    return {
        **record,
        "actual_profit": profit,
        "actual_margin": round(profit / float(sale_price) * 100, 2)
        if sale_price
        else 0.0,
    }


def _row_to_record(row) -> dict[str, Any]:
    return calculate_actual_profit(
        {
            "status": row["status"],
            "actual_purchase_price": row["actual_purchase_price"],
            "actual_sale_price": row["actual_sale_price"],
            "actual_platform_fee": row["actual_platform_fee"],
            "actual_shipping_cost": row["actual_shipping_cost"],
            "actual_other_cost": row["actual_other_cost"],
            "notes": row["notes"],
            "purchased_at": row["purchased_at"],
            "listed_at": row["listed_at"],
            "sold_at": row["sold_at"],
            "updated_at": row["updated_at"],
        }
    )


def load_inventory_records(
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
        condition += " AND item_id IN (" + ", ".join("?" for _ in normalized_ids) + ")"
        params.extend(normalized_ids)

    with sqlite_connection() as conn:
        rows = conn.execute(
            f"SELECT * FROM inventory_records WHERE {condition}", tuple(params)
        ).fetchall()
    return {str(row["item_id"]): _row_to_record(row) for row in rows}


def save_inventory_record(
    result_filename: str, item_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    normalized_item_id = str(item_id or "").strip()
    if not normalized_item_id:
        raise ValueError("商品缺少商品 ID，无法保存经营台账。")

    bootstrap_sqlite_storage()
    now = datetime.now().isoformat(timespec="seconds")
    with sqlite_connection() as conn:
        existing = conn.execute(
            """
            SELECT * FROM inventory_records
            WHERE result_filename = ? AND item_id = ?
            """,
            (result_filename, normalized_item_id),
        ).fetchone()
        current = _row_to_record(existing) if existing is not None else {
            "status": "discovered",
            "actual_purchase_price": None,
            "actual_sale_price": None,
            "actual_platform_fee": 0.0,
            "actual_shipping_cost": 0.0,
            "actual_other_cost": 0.0,
            "notes": "",
            "purchased_at": None,
            "listed_at": None,
            "sold_at": None,
        }

        status = _normalize_status(payload.get("status", current["status"]))
        values = {
            field: _as_amount(
                payload[field] if field in payload else current[field],
                field,
                allow_none=field in OPTIONAL_AMOUNT_FIELDS,
            )
            for field in (*OPTIONAL_AMOUNT_FIELDS, *COST_FIELDS)
        }
        notes = str(payload.get("notes", current["notes"]) or "").strip()
        timestamps = {
            "purchased_at": current["purchased_at"],
            "listed_at": current["listed_at"],
            "sold_at": current["sold_at"],
        }
        if status == "purchased" and not timestamps["purchased_at"]:
            timestamps["purchased_at"] = now
        if status == "listed" and not timestamps["listed_at"]:
            timestamps["listed_at"] = now
        if status == "sold" and not timestamps["sold_at"]:
            timestamps["sold_at"] = now

        conn.execute(
            """
            INSERT INTO inventory_records (
                result_filename, item_id, status, actual_purchase_price,
                actual_sale_price, actual_platform_fee, actual_shipping_cost,
                actual_other_cost, notes, purchased_at, listed_at, sold_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(result_filename, item_id) DO UPDATE SET
                status = excluded.status,
                actual_purchase_price = excluded.actual_purchase_price,
                actual_sale_price = excluded.actual_sale_price,
                actual_platform_fee = excluded.actual_platform_fee,
                actual_shipping_cost = excluded.actual_shipping_cost,
                actual_other_cost = excluded.actual_other_cost,
                notes = excluded.notes,
                purchased_at = excluded.purchased_at,
                listed_at = excluded.listed_at,
                sold_at = excluded.sold_at,
                updated_at = excluded.updated_at
            """,
            (
                result_filename,
                normalized_item_id,
                status,
                values["actual_purchase_price"],
                values["actual_sale_price"],
                values["actual_platform_fee"],
                values["actual_shipping_cost"],
                values["actual_other_cost"],
                notes,
                timestamps["purchased_at"],
                timestamps["listed_at"],
                timestamps["sold_at"],
                now,
            ),
        )
        conn.commit()
    return calculate_actual_profit(
        {
            "status": status,
            **values,
            "notes": notes,
            **timestamps,
            "updated_at": now,
        }
    )
