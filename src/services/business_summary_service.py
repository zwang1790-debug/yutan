"""Aggregate inventory records into seller-facing operating metrics."""
from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Any

from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.infrastructure.persistence.sqlite_connection import sqlite_connection
from src.services.inventory_service import calculate_actual_profit
from src.services.price_history_service import normalize_model_key


STATUS_ORDER = ("discovered", "contacting", "purchased", "listed", "sold", "skipped")
OWNED_STATUSES = {"purchased", "listed", "sold"}
OPEN_INVENTORY_STATUSES = {"purchased", "listed"}


def _as_number(value: Any) -> float:
    return round(float(value or 0), 2)


def _days_between(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    try:
        days = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds() / 86400
    except (TypeError, ValueError):
        return None
    return round(max(0, days), 1)


def _row_to_inventory(row) -> dict[str, Any]:
    return calculate_actual_profit(
        {
            "status": row["status"],
            "actual_purchase_price": row["actual_purchase_price"],
            "actual_sale_price": row["actual_sale_price"],
            "actual_platform_fee": row["actual_platform_fee"],
            "actual_shipping_cost": row["actual_shipping_cost"],
            "actual_other_cost": row["actual_other_cost"],
            "purchased_at": row["purchased_at"],
            "listed_at": row["listed_at"],
            "sold_at": row["sold_at"],
        }
    )


def _empty_summary() -> dict[str, Any]:
    return {
        "tracked_items": 0,
        "status_counts": {status: 0 for status in STATUS_ORDER},
        "owned_items": 0,
        "open_inventory_items": 0,
        "capital_deployed": 0.0,
        "open_inventory_cost": 0.0,
        "sold_items": 0,
        "settled_sales": 0.0,
        "realized_profit": 0.0,
        "realized_roi": None,
        "average_turnover_days": None,
        "turnover_sample_count": 0,
        "incomplete_sold_items": 0,
        "model_performance": [],
    }


def _load_result_business_summary_sync(
    result_filename: str, visible_item_ids: set[str] | None = None
) -> dict[str, Any]:
    bootstrap_sqlite_storage()
    with sqlite_connection() as conn:
        params: list[Any] = [result_filename]
        item_condition = ""
        if visible_item_ids is not None:
            normalized_ids = sorted(str(item_id).strip() for item_id in visible_item_ids if str(item_id).strip())
            if not normalized_ids:
                return _empty_summary()
            item_condition = " AND inventory_records.item_id IN (" + ",".join("?" for _ in normalized_ids) + ")"
            params.extend(normalized_ids)
        rows = conn.execute(
            """
            SELECT
                inventory_records.*, result_items.title
            FROM inventory_records
            LEFT JOIN result_items
              ON result_items.result_filename = inventory_records.result_filename
             AND result_items.item_id = inventory_records.item_id
            WHERE inventory_records.result_filename = ?
            """ + item_condition + """
            ORDER BY inventory_records.updated_at DESC
            """,
            tuple(params),
        ).fetchall()

    summary = _empty_summary()
    model_groups: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "model_key": "",
            "sold_items": 0,
            "settled_sales": 0.0,
            "realized_cost": 0.0,
            "realized_profit": 0.0,
            "turnover_days": [],
        }
    )
    turnover_days: list[float] = []

    for row in rows:
        record = _row_to_inventory(row)
        status = record["status"]
        summary["tracked_items"] += 1
        summary["status_counts"][status] += 1
        purchase_price = record["actual_purchase_price"]
        sale_price = record["actual_sale_price"]

        if status in OWNED_STATUSES:
            summary["owned_items"] += 1
            summary["capital_deployed"] += _as_number(purchase_price)
        if status in OPEN_INVENTORY_STATUSES:
            summary["open_inventory_items"] += 1
            summary["open_inventory_cost"] += _as_number(purchase_price)

        if status != "sold":
            continue
        summary["sold_items"] += 1
        if purchase_price is None or sale_price is None:
            summary["incomplete_sold_items"] += 1
            continue

        summary["settled_sales"] += _as_number(sale_price)
        summary["realized_profit"] += _as_number(record["actual_profit"])
        model_key = normalize_model_key(row["title"]) or str(row["title"] or "未识别型号")
        group = model_groups[model_key]
        group["model_key"] = model_key
        group["sold_items"] += 1
        group["settled_sales"] += _as_number(sale_price)
        group["realized_cost"] += _as_number(purchase_price)
        group["realized_profit"] += _as_number(record["actual_profit"])
        turnover = _days_between(record.get("purchased_at"), record.get("sold_at"))
        if turnover is not None:
            turnover_days.append(turnover)
            group["turnover_days"].append(turnover)

    realized_cost = sum(
        group["realized_cost"] for group in model_groups.values()
    )
    summary["capital_deployed"] = round(summary["capital_deployed"], 2)
    summary["open_inventory_cost"] = round(summary["open_inventory_cost"], 2)
    summary["settled_sales"] = round(summary["settled_sales"], 2)
    summary["realized_profit"] = round(summary["realized_profit"], 2)
    summary["realized_roi"] = (
        round(summary["realized_profit"] / realized_cost * 100, 2)
        if realized_cost > 0
        else None
    )
    summary["turnover_sample_count"] = len(turnover_days)
    summary["average_turnover_days"] = (
        round(sum(turnover_days) / len(turnover_days), 1) if turnover_days else None
    )
    performance = []
    for group in model_groups.values():
        cost = group["realized_cost"]
        samples = group["turnover_days"]
        performance.append(
            {
                "model_key": group["model_key"],
                "sold_items": group["sold_items"],
                "settled_sales": round(group["settled_sales"], 2),
                "realized_profit": round(group["realized_profit"], 2),
                "roi": round(group["realized_profit"] / cost * 100, 2) if cost else None,
                "average_turnover_days": round(sum(samples) / len(samples), 1) if samples else None,
            }
        )
    summary["model_performance"] = sorted(
        performance,
        key=lambda item: (item["realized_profit"], item["settled_sales"]),
        reverse=True,
    )[:8]
    return summary


async def load_result_business_summary(
    result_filename: str, visible_item_ids: set[str] | None = None
) -> dict[str, Any]:
    return await asyncio.to_thread(
        _load_result_business_summary_sync, result_filename, visible_item_ids
    )
