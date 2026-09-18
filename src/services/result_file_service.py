"""
结果记录富化与文件名校验服务
"""

from src.infrastructure.persistence.storage_names import normalize_keyword_from_filename
from src.services.price_history_service import (
    build_item_price_context,
    load_price_snapshots,
    parse_price_value,
)
from src.services.result_storage_service import load_visible_result_item_ids
from src.services.inventory_service import load_inventory_records
from src.services.opportunity_score_service import build_opportunity_assessment
from src.services.profit_estimate_service import load_profit_estimates
from src.services.pricing_service import build_pricing_assessment


def validate_result_filename(filename: str) -> None:
    if not filename.endswith(".jsonl") or "/" in filename or ".." in filename:
        raise ValueError("无效的文件名")


def enrich_records_with_price_insight(records: list[dict], filename: str) -> list[dict]:
    estimates = load_profit_estimates(
        filename,
        [
            str((record.get("商品信息", {}) or {}).get("商品ID") or "")
            for record in records
        ],
    )
    inventory_records = load_inventory_records(
        filename,
        [
            str((record.get("商品信息", {}) or {}).get("商品ID") or "")
            for record in records
        ],
    )
    snapshots = load_price_snapshots(normalize_keyword_from_filename(filename))
    if not snapshots:
        return _attach_commercial_records(records, estimates, inventory_records)

    visible_item_ids = load_visible_result_item_ids(filename)
    visible_snapshots = [
        snapshot
        for snapshot in snapshots
        if str(snapshot.get("item_id") or "") in visible_item_ids
    ]
    enriched = []
    for record in records:
        info = record.get("商品信息", {}) or {}
        clone = dict(record)
        clone["price_insight"] = build_item_price_context(
            snapshots,
            item_id=str(info.get("商品ID") or ""),
            current_price=parse_price_value(info.get("当前售价")),
            item_title=info.get("商品标题"),
            market_snapshots=snapshots,
        )
        clone["pricing_assessment"] = build_pricing_assessment(clone, clone["price_insight"])
        clone["opportunity_assessment"] = build_opportunity_assessment(
            clone, clone["price_insight"]
        )
        item_id = str(info.get("商品ID") or "")
        if item_id in estimates:
            clone["profit_estimate"] = estimates[item_id]
        if item_id in inventory_records:
            clone["inventory_record"] = inventory_records[item_id]
        enriched.append(clone)
    return enriched


def _attach_commercial_records(
    records: list[dict],
    estimates: dict[str, dict],
    inventory_records: dict[str, dict],
) -> list[dict]:
    enriched = []
    for record in records:
        info = record.get("商品信息", {}) or {}
        item_id = str(info.get("商品ID") or "")
        clone = dict(record)
        clone["opportunity_assessment"] = build_opportunity_assessment(clone, None)
        clone["pricing_assessment"] = build_pricing_assessment(clone, None)
        if item_id in estimates:
            clone["profit_estimate"] = estimates[item_id]
        if item_id in inventory_records:
            clone["inventory_record"] = inventory_records[item_id]
        enriched.append(clone)
    return enriched
