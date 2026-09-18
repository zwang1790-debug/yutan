"""
价格历史记录与聚合服务
"""
from __future__ import annotations

import json
import math
import os
import re
from collections import defaultdict
from datetime import datetime
from statistics import median
from typing import Any, Iterable, Optional

from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.infrastructure.persistence.sqlite_connection import sqlite_connection

PRICE_HISTORY_DIR = "price_history"
DEFAULT_HISTORY_WINDOW_DAYS = 30
GPU_VALUATION_WINDOW_DAYS = 30
GPU_VALUATION_HALF_LIFE_DAYS = 14
GPU_MIN_VALID_SAMPLES = 5
GPU_RISK_KEYWORDS = (
    "维修", "修过", "矿卡", "挖矿", "矿场", "故障", "暗病", "进水",
    "烧供电", "烧", "花屏", "点不亮", "不开机", "配件机", "尸体",
    "改bios", "拆机维修", "拆机卡",
)
GPU_NON_RETAIL_KEYWORDS = ("笔记本", "移动版", "m版", "3070m", "3060m", "3050m")


def normalize_keyword_slug(keyword: str) -> str:
    text = "".join(
        char for char in str(keyword or "").lower().replace(" ", "_")
        if char.isalnum() or char in "_-"
    ).rstrip("_")
    return text or "unknown"


def build_price_history_path(keyword: str) -> str:
    return os.path.join(
        PRICE_HISTORY_DIR,
        f"{normalize_keyword_slug(keyword)}_history.jsonl",
    )


def parse_price_value(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)

    text = str(value).strip().replace("¥", "").replace(",", "")
    if not text or text in {"价格异常", "暂无", "-", "N/A"}:
        return None
    if text.endswith("万"):
        text = str(float(text[:-1]) * 10000)
    try:
        return round(float(text), 2)
    except (TypeError, ValueError):
        return None


def normalize_model_key(title: Any) -> str:
    """Build a conservative comparable-model key from a listing title."""
    text = str(title or "").lower()
    gpu = re.search(r"(?:^|[^a-z])(rtx|gtx|rx)\s*([0-9]{3,4})(?:\s*(ti|super))?(?:$|[^a-z0-9])", text)
    if gpu:
        vram = re.search(r"\b(\d{1,2})\s*g(?:b)?\b", text)
        variant = f" {gpu.group(3)}" if gpu.group(3) else ""
        return f"{gpu.group(1)} {gpu.group(2)}{variant}" + (f" {vram.group(1)}g" if vram else "")

    apple_laptop = re.search(r"\b(macbook)\s+(air|pro)\s+(m[1-4](?:\s+pro|\s+max)?)\b", text)
    if apple_laptop:
        capacity = re.search(r"\b(\d{1,2})\s*(?:\+|g(?:b)?\s*[+/])\s*(\d{3,4})\s*g?(?:b)?\b", text)
        suffix = f" {capacity.group(1)}g {capacity.group(2)}g" if capacity else ""
        return f"{apple_laptop.group(1)} {apple_laptop.group(2)} {apple_laptop.group(3).replace(' ', '')}{suffix}"

    iphone = re.search(r"\b(iphone)\s*(1[1-6]|se\s*[2-3])\s*(pro\s*max|pro|plus|mini)?\b", text)
    if iphone:
        variant = (iphone.group(3) or "").replace(" ", "")
        storage = re.search(r"\b(64|128|256|512|1024)\s*g(?:b)?\b", text)
        return " ".join(part for part in [iphone.group(1), iphone.group(2), variant, f"{storage.group(1)}g" if storage else ""] if part)

    # Keep a useful fallback for non-GPU categories and existing tests.
    tokens = re.findall(r"[a-z]+[0-9]+[a-z0-9]*|[a-z]{2,}", text)
    return " ".join(tokens[:4])


def _same_model_records(records: Iterable[dict], model_key: str) -> list[dict]:
    if not model_key:
        return list(records)
    return [
        record
        for record in records
        if normalize_model_key(record.get("title")) == model_key
    ]


def _is_gpu_model_key(model_key: str) -> bool:
    return bool(re.match(r"^(?:rtx|gtx|rx) \d{3,4}", model_key or ""))


def _gpu_listing_is_risky(record: dict) -> bool:
    text = " ".join(
        [
            str(record.get("title") or "").lower(),
            " ".join(str(tag).lower() for tag in (record.get("tags") or [])),
        ]
    )
    return bool(extract_gpu_risk_signals(text)) or any(keyword in text for keyword in GPU_NON_RETAIL_KEYWORDS)


def extract_gpu_risk_signals(text: str) -> list[str]:
    """Return positive GPU risk phrases while respecting common negations."""
    signals = []
    normalized = str(text or "").lower()
    for keyword in GPU_RISK_KEYWORDS:
        start = 0
        while True:
            index = normalized.find(keyword.lower(), start)
            if index < 0:
                break
            prefix = normalized[max(0, index - 3):index]
            if not re.search(r"(?:非|无|没有|未|不|没)\s*$", prefix):
                signals.append(keyword)
                break
            start = index + len(keyword)
    return signals


def _safe_iso_datetime(value: Optional[str]) -> str:
    if value:
        return value
    return datetime.now().isoformat()


def _to_day(iso_text: str) -> str:
    return iso_text[:10]


def _build_snapshot_record(
    *,
    keyword: str,
    task_name: str,
    item: dict,
    run_id: str,
    snapshot_time: str,
) -> Optional[dict]:
    item_id = str(item.get("商品ID") or "").strip()
    link = str(item.get("商品链接") or "").strip()
    unique_id = item_id or link
    price_value = parse_price_value(item.get("当前售价"))
    if not unique_id or price_value is None:
        return None

    return {
        "snapshot_time": snapshot_time,
        "snapshot_day": _to_day(snapshot_time),
        "run_id": run_id,
        "task_name": task_name,
        "keyword": keyword,
        "item_id": unique_id,
        "title": item.get("商品标题") or "",
        "price": price_value,
        "price_display": item.get("当前售价") or "",
        "tags": item.get("商品标签") or [],
        "region": item.get("发货地区") or "",
        "seller": item.get("卖家昵称") or "",
        "publish_time": item.get("发布时间") or "",
        "link": link,
    }


def record_market_snapshots(
    *,
    keyword: str,
    task_name: str,
    items: Iterable[dict],
    run_id: str,
    snapshot_time: Optional[str] = None,
    seen_item_ids: Optional[set[str]] = None,
) -> list[dict]:
    snapshot_time = _safe_iso_datetime(snapshot_time)
    seen = seen_item_ids if seen_item_ids is not None else set()
    records: list[dict] = []

    for item in items:
        record = _build_snapshot_record(
            keyword=keyword,
            task_name=task_name,
            item=item,
            run_id=run_id,
            snapshot_time=snapshot_time,
        )
        if record is None or record["item_id"] in seen:
            continue
        seen.add(record["item_id"])
        records.append(record)

    if not records:
        return []

    bootstrap_sqlite_storage()
    keyword_slug = normalize_keyword_slug(keyword)
    with sqlite_connection() as conn:
        for record in records:
            conn.execute(
                """
                INSERT OR IGNORE INTO price_snapshots (
                    keyword_slug, keyword, task_name, snapshot_time, snapshot_day,
                    run_id, item_id, title, price, price_display, tags_json, region,
                    seller, publish_time, link
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    keyword_slug,
                    record.get("keyword", keyword),
                    record.get("task_name", task_name),
                    record.get("snapshot_time", snapshot_time),
                    record.get("snapshot_day", _to_day(snapshot_time)),
                    record.get("run_id", run_id),
                    record.get("item_id", ""),
                    record.get("title", ""),
                    record.get("price"),
                    record.get("price_display", ""),
                    json.dumps(record.get("tags") or [], ensure_ascii=False),
                    record.get("region", ""),
                    record.get("seller", ""),
                    record.get("publish_time", ""),
                    record.get("link", ""),
                ),
            )
        conn.commit()
    return records


def load_price_snapshots(keyword: str) -> list[dict]:
    bootstrap_sqlite_storage()
    with sqlite_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM price_snapshots
            WHERE keyword_slug = ?
            ORDER BY snapshot_time ASC, id ASC
            """,
            (normalize_keyword_slug(keyword),),
        ).fetchall()
    snapshots: list[dict] = []
    for row in rows:
        snapshots.append(
            {
                "snapshot_time": row["snapshot_time"],
                "snapshot_day": row["snapshot_day"],
                "run_id": row["run_id"],
                "task_name": row["task_name"],
                "keyword": row["keyword"],
                "item_id": row["item_id"],
                "title": row["title"],
                "price": row["price"],
                "price_display": row["price_display"],
                "tags": json.loads(row["tags_json"] or "[]"),
                "region": row["region"],
                "seller": row["seller"],
                "publish_time": row["publish_time"],
                "link": row["link"],
            }
        )
    return snapshots


def delete_price_snapshots(keyword: str) -> int:
    bootstrap_sqlite_storage()
    with sqlite_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM price_snapshots WHERE keyword_slug = ?",
            (normalize_keyword_slug(keyword),),
        )
        conn.commit()
    return int(cursor.rowcount or 0)


def _dedupe_latest(records: Iterable[dict], group_key: str) -> list[dict]:
    latest_by_key: dict[str, dict] = {}
    for record in records:
        key = str(record.get(group_key) or "").strip()
        if not key:
            continue
        latest_by_key[key] = record
    return list(latest_by_key.values())


def _summarize_prices(records: Iterable[dict]) -> dict:
    entries = [record for record in records if parse_price_value(record.get("price")) is not None]
    prices = [float(record["price"]) for record in entries]
    if not prices:
        return {
            "sample_count": 0,
            "avg_price": None,
            "median_price": None,
            "min_price": None,
            "max_price": None,
        }

    return {
        "sample_count": len(prices),
        "avg_price": round(sum(prices) / len(prices), 2),
        "median_price": round(float(median(prices)), 2),
        "min_price": round(min(prices), 2),
        "max_price": round(max(prices), 2),
    }


def _weighted_quantile(values: list[tuple[float, float]], quantile: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values, key=lambda entry: entry[0])
    total_weight = sum(weight for _, weight in ordered)
    threshold = total_weight * quantile
    cumulative = 0.0
    for price, weight in ordered:
        cumulative += weight
        if cumulative >= threshold:
            return round(price, 2)
    return round(ordered[-1][0], 2)


def build_gpu_market_valuation(
    snapshots: Iterable[dict],
    model_key: str,
    *,
    as_of: Optional[str] = None,
) -> Optional[dict]:
    """Build a conservative 30-day GPU price band from clean comparable listings."""
    if not _is_gpu_model_key(model_key):
        return None

    records = _same_model_records(snapshots, model_key)
    if not records:
        return {
            "is_eligible": False,
            "sample_count": 0,
            "raw_sample_count": 0,
            "excluded_sample_count": 0,
            "p25_price": None,
            "p35_price": None,
            "p50_price": None,
            "p75_price": None,
            "window_days": GPU_VALUATION_WINDOW_DAYS,
        }

    latest_time = as_of or max(str(record.get("snapshot_time") or "") for record in records)
    latest_dt = datetime.fromisoformat(latest_time)
    latest_by_item = _dedupe_latest(records, "item_id")
    in_window = []
    for record in latest_by_item:
        snapshot_time = str(record.get("snapshot_time") or "")
        try:
            age_days = max(0.0, (latest_dt - datetime.fromisoformat(snapshot_time)).total_seconds() / 86400)
        except ValueError:
            continue
        if age_days <= GPU_VALUATION_WINDOW_DAYS:
            in_window.append((record, age_days))

    valid = [entry for entry in in_window if not _gpu_listing_is_risky(entry[0])]
    weighted_prices = [
        (float(record["price"]), math.exp(-math.log(2) * age_days / GPU_VALUATION_HALF_LIFE_DAYS))
        for record, age_days in valid
        if parse_price_value(record.get("price")) is not None
    ]
    prices = [price for price, _ in weighted_prices]
    if len(prices) >= 4:
        center = float(median(prices))
        mad = float(median([abs(price - center) for price in prices]))
        if mad > 0:
            max_deviation = 3.5 * 1.4826 * mad
            weighted_prices = [
                entry for entry in weighted_prices if abs(entry[0] - center) <= max_deviation
            ]

    sample_count = len(weighted_prices)
    return {
        "is_eligible": sample_count >= GPU_MIN_VALID_SAMPLES,
        "sample_count": sample_count,
        "raw_sample_count": len(in_window),
        "excluded_sample_count": max(0, len(in_window) - sample_count),
        "p25_price": _weighted_quantile(weighted_prices, 0.25),
        "p35_price": _weighted_quantile(weighted_prices, 0.35),
        "p50_price": _weighted_quantile(weighted_prices, 0.50),
        "p75_price": _weighted_quantile(weighted_prices, 0.75),
        "window_days": GPU_VALUATION_WINDOW_DAYS,
    }


def _build_daily_trend(snapshots: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for snapshot in snapshots:
        grouped[str(snapshot.get("snapshot_day") or "")].append(snapshot)

    points: list[dict] = []
    for day in sorted(grouped.keys()):
        day_records = _dedupe_latest(grouped[day], "item_id")
        summary = _summarize_prices(day_records)
        summary["day"] = day
        points.append(summary)
    return points


def _recent_window_snapshots(snapshots: list[dict], window_days: int) -> list[dict]:
    if not snapshots:
        return []
    latest_time = max(str(record.get("snapshot_time") or "") for record in snapshots)
    latest_dt = datetime.fromisoformat(latest_time)
    filtered = []
    for record in snapshots:
        current_time = datetime.fromisoformat(str(record.get("snapshot_time") or latest_time))
        if (latest_dt - current_time).days <= max(0, window_days):
            filtered.append(record)
    return filtered


def _resolve_deal_label(score: int) -> str:
    if score >= 65:
        return "高性价比"
    if score >= 50:
        return "值得关注"
    if score >= 40:
        return "价格正常"
    return "价格偏高"


def build_item_price_context(
    snapshots: list[dict],
    *,
    item_id: str,
    current_price: Optional[float],
    item_title: Optional[str] = None,
    market_snapshots: Optional[list[dict]] = None,
) -> dict:
    if not item_id:
        return {"observation_count": 0, "deal_score": None, "deal_label": "暂无数据"}

    item_snapshots = [record for record in snapshots if str(record.get("item_id")) == str(item_id)]
    if not item_snapshots and (current_price is None or not item_title):
        return {"observation_count": 0, "deal_score": None, "deal_label": "暂无数据"}

    latest_item_snapshot = item_snapshots[-1] if item_snapshots else {}
    price_now = current_price if current_price is not None else parse_price_value(latest_item_snapshot.get("price"))
    historical_prices = [float(record["price"]) for record in item_snapshots if parse_price_value(record.get("price")) is not None]
    model_key = normalize_model_key(item_title or latest_item_snapshot.get("title"))
    source_snapshots = market_snapshots if market_snapshots is not None else snapshots
    latest_run_id = str(source_snapshots[-1].get("run_id") or "") if source_snapshots else ""
    latest_market = _dedupe_latest(
        _same_model_records(
            [record for record in source_snapshots if str(record.get("run_id") or "") == latest_run_id],
            model_key,
        ),
        "item_id",
    )
    market_summary = _summarize_prices(latest_market)
    market_avg = market_summary.get("avg_price")
    market_median = market_summary.get("median_price")
    gpu_valuation = build_gpu_market_valuation(source_snapshots, model_key)
    if gpu_valuation is not None:
        market_avg = gpu_valuation["p50_price"] if gpu_valuation["is_eligible"] else None
        market_median = market_avg

    score = 50
    if price_now is not None and market_avg:
        score += int(((market_avg - price_now) / market_avg) * 60)
    if price_now is not None and historical_prices:
        historical_max = max(historical_prices)
        if historical_max > 0:
            score += int(((historical_max - price_now) / historical_max) * 20)
        if math.isclose(price_now, min(historical_prices), rel_tol=0.001):
            score += 8
    score = max(0, min(100, score))

    previous_price = historical_prices[-2] if len(historical_prices) >= 2 else None
    change_amount = None if previous_price is None or price_now is None else round(price_now - previous_price, 2)
    change_percent = None
    if change_amount is not None and previous_price:
        change_percent = round(change_amount / previous_price * 100, 2)

    return {
        "observation_count": len(historical_prices),
        "current_price": price_now,
        "avg_price": round(sum(historical_prices) / len(historical_prices), 2) if historical_prices else None,
        "median_price": round(float(median(historical_prices)), 2) if historical_prices else None,
        "min_price": round(min(historical_prices), 2) if historical_prices else None,
        "max_price": round(max(historical_prices), 2) if historical_prices else None,
        "first_seen_at": item_snapshots[0].get("snapshot_time") if item_snapshots else None,
        "last_seen_at": latest_item_snapshot.get("snapshot_time") if item_snapshots else None,
        "market_avg_price": market_avg,
        "market_median_price": market_median,
        "market_sample_count": (
            gpu_valuation["sample_count"] if gpu_valuation is not None else market_summary.get("sample_count", 0)
        ),
        "market_raw_sample_count": (
            gpu_valuation["raw_sample_count"] if gpu_valuation is not None else market_summary.get("sample_count", 0)
        ),
        "market_p25_price": gpu_valuation["p25_price"] if gpu_valuation else None,
        "market_p35_price": gpu_valuation["p35_price"] if gpu_valuation else None,
        "market_p50_price": gpu_valuation["p50_price"] if gpu_valuation else market_median,
        "market_p75_price": gpu_valuation["p75_price"] if gpu_valuation else None,
        "market_valuation_eligible": gpu_valuation["is_eligible"] if gpu_valuation else bool(market_median),
        "market_excluded_sample_count": gpu_valuation["excluded_sample_count"] if gpu_valuation else 0,
        "market_valuation_window_days": gpu_valuation["window_days"] if gpu_valuation else None,
        "market_model_key": model_key or None,
        "price_change_amount": change_amount,
        "price_change_percent": change_percent,
        "deal_score": score,
        "deal_label": _resolve_deal_label(score),
    }


def build_market_reference(
    *,
    keyword: str,
    item: dict,
    current_market_items: list[dict],
    historical_snapshots: list[dict],
) -> dict:
    current_market_records = []
    for market_item in current_market_items:
        price = parse_price_value(market_item.get("当前售价"))
        if price is None:
            continue
        current_market_records.append({"price": price})

    model_key = normalize_model_key(item.get("商品标题"))
    comparable_current_items = _same_model_records(
        [
            {"price": price, "title": market_item.get("商品标题", "")}
            for market_item in current_market_items
            if (price := parse_price_value(market_item.get("当前售价"))) is not None
        ],
        model_key,
    )
    market_snapshot = _summarize_prices(comparable_current_items)
    comparable_history = _same_model_records(historical_snapshots, model_key)
    history_summary = _summarize_prices(_dedupe_latest(comparable_history, "item_id"))
    item_context = build_item_price_context(
        historical_snapshots,
        item_id=str(item.get("商品ID") or ""),
        current_price=parse_price_value(item.get("当前售价")),
        item_title=item.get("商品标题"),
        market_snapshots=comparable_history,
    )
    return {
        "当前搜索样本": market_snapshot,
        "历史价格概览": history_summary,
        "可比型号": model_key or "未识别型号",
        "本商品价格位置": item_context,
        "关键词": keyword,
    }


def build_price_history_insights(
    keyword: str,
    *,
    window_days: int = DEFAULT_HISTORY_WINDOW_DAYS,
    visible_item_ids: Optional[set[str]] = None,
) -> dict:
    snapshots = load_price_snapshots(keyword)
    if visible_item_ids is not None:
        snapshots = [
            snapshot
            for snapshot in snapshots
            if str(snapshot.get("item_id") or "") in visible_item_ids
        ]
    if not snapshots:
        return {
            "market_summary": _summarize_prices([]),
            "history_summary": {"unique_items": 0, **_summarize_prices([])},
            "daily_trend": [],
            "latest_snapshot_at": None,
        }

    recent_snapshots = _recent_window_snapshots(snapshots, window_days)
    latest_run_id = str(snapshots[-1].get("run_id") or "")
    latest_run_snapshots = _dedupe_latest(
        [record for record in snapshots if str(record.get("run_id") or "") == latest_run_id],
        "item_id",
    )
    latest_records_by_item = _dedupe_latest(recent_snapshots, "item_id")
    grouped_market_summary = {}
    for record in latest_run_snapshots:
        model_key = normalize_model_key(record.get("title")) or "未识别型号"
        grouped_market_summary.setdefault(model_key, []).append(record)

    return {
        "market_summary": {
            **_summarize_prices(latest_run_snapshots),
            "snapshot_time": snapshots[-1].get("snapshot_time"),
            "scope": "关键词总览（商品卡片使用可比型号均价）",
        },
        "market_groups": {
            key: _summarize_prices(value) for key, value in sorted(grouped_market_summary.items())
        },
        "history_summary": {
            "unique_items": len(latest_records_by_item),
            **_summarize_prices(latest_records_by_item),
        },
        "daily_trend": _build_daily_trend(recent_snapshots),
        "latest_snapshot_at": snapshots[-1].get("snapshot_time"),
    }
