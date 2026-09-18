"""Explainable resale pricing policy built on market price bands."""
from __future__ import annotations

import math
import re
from typing import Any

from src.services.price_history_service import extract_gpu_risk_signals, normalize_model_key

GPU_MODEL_PATTERN = re.compile(r"^(?:rtx|gtx|rx) \d{3,4}")
GPU_MIN_BAND_SAMPLES = 5
GPU_MIN_QUOTE_SAMPLES = 10
GPU_HIGH_CONFIDENCE_SAMPLES = 15
GENERIC_MIN_QUOTE_SAMPLES = 5
PLATFORM_FEE_RATE = 0.05
INSPECTION_RESERVE_RATE = 0.03
AFTER_SALE_RESERVE_RATE = 0.03
TARGET_MARGIN_RATE = 0.12
MIN_TARGET_PROFIT = 200.0
LOGISTICS_RESERVE = 30.0
RISK_KEYWORDS = ("维修", "修过", "矿卡", "挖矿", "矿场", "故障", "暗病", "进水", "烧供电", "烧", "花屏", "点不亮", "不开机", "配件机", "尸体", "监管机", "翻新", "租赁", "拆机维修", "拆机卡")
POSITIVE_CONDITION_SIGNALS = (("全新", 0.03), ("保修", 0.03), ("购买凭证", 0.03), ("无拆无修", 0.02), ("功能正常", 0.02), ("个人自用", 0.02))
NEGATIVE_CONDITION_SIGNALS = (("明显使用痕迹", -0.05), ("成色一般", -0.04), ("无盒", -0.03), ("缺配件", -0.05))


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 2) if math.isfinite(number) else None


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def extract_risk_notes(record: dict) -> list[str]:
    analysis = record.get("ai_analysis", {}) or {}
    tags = [str(tag).strip() for tag in (analysis.get("risk_tags") or []) if str(tag).strip()]
    title = str((record.get("商品信息", {}) or {}).get("商品标题") or "")
    for keyword in extract_gpu_risk_signals(title):
        if keyword not in tags:
            tags.append(keyword)
    for keyword in RISK_KEYWORDS:
        if keyword in tags:
            continue
        if keyword in {"维修", "修过", "矿卡", "挖矿", "矿场", "故障", "暗病", "进水", "烧供电", "烧", "花屏", "点不亮", "不开机", "配件机", "尸体", "拆机维修", "拆机卡"}:
            continue
        if keyword.lower() in title.lower():
            tags.append(keyword)
    return tags[:6]


def _condition_adjustment(record: dict) -> tuple[float, list[str]]:
    info = record.get("商品信息", {}) or {}
    analysis = record.get("ai_analysis", {}) or {}
    text = " ".join([str(info.get("商品标题") or ""), str(analysis.get("reason") or ""), " ".join(str(tag) for tag in (info.get("商品标签") or []))]).lower()
    adjustment = 0.0
    signals: list[str] = []
    for signal, value in POSITIVE_CONDITION_SIGNALS:
        if signal.lower() in text:
            adjustment += value
            signals.append(f"{signal}+{value * 100:.0f}%")
    for signal, value in NEGATIVE_CONDITION_SIGNALS:
        if signal.lower() in text:
            adjustment += value
            signals.append(f"{signal}{value * 100:.0f}%")
    return round(_clamp(adjustment, -0.10, 0.05), 4), signals


def _empty_pricing(status: str, label: str, confidence: str, reason: str, current_price: float | None, market_samples: int, raw_samples: int, excluded_samples: int, risk_notes: list[str], is_gpu: bool, price_band: dict | None = None) -> dict:
    return {
        "status": status, "label": label, "can_buy": False, "confidence": confidence, "is_gpu": is_gpu,
        "market_sample_count": market_samples, "market_raw_sample_count": raw_samples,
        "market_excluded_sample_count": excluded_samples,
        "min_samples_for_quote": GPU_MIN_QUOTE_SAMPLES if is_gpu else GENERIC_MIN_QUOTE_SAMPLES,
        "price_band": price_band or {"p25": None, "p35": None, "p50": None, "p75": None},
        "quick_sale_price": None, "conservative_resale_price": None, "suggested_listing_price": None,
        "recommended_max_purchase_price": None, "expected_profit": None, "expected_margin": None,
        "state_adjustment_rate": 0.0, "state_adjustment_signals": [], "cost_breakdown": {},
        "current_price": current_price, "gap_to_max_purchase_price": None,
        "reasons": [reason], "risk_notes": risk_notes,
    }


def build_pricing_assessment(record: dict, price_insight: dict | None) -> dict:
    insight = price_insight or {}
    info = record.get("商品信息", {}) or {}
    current_price = _number(insight.get("current_price"))
    risk_notes = extract_risk_notes(record)
    model_key = str(insight.get("market_model_key") or normalize_model_key(info.get("商品标题")) or "")
    is_gpu = bool(GPU_MODEL_PATTERN.match(model_key))
    p25 = _number(insight.get("market_p25_price"))
    p35 = _number(insight.get("market_p35_price"))
    p50 = _number(insight.get("market_p50_price")) or _number(insight.get("market_median_price")) or _number(insight.get("market_avg_price"))
    p75 = _number(insight.get("market_p75_price"))
    try:
        market_samples = max(0, int(insight.get("market_sample_count") or 0))
    except (TypeError, ValueError):
        market_samples = 0
    try:
        raw_samples = max(market_samples, int(insight.get("market_raw_sample_count") or market_samples))
    except (TypeError, ValueError):
        raw_samples = market_samples
    try:
        excluded_samples = max(0, int(insight.get("market_excluded_sample_count") or 0))
    except (TypeError, ValueError):
        excluded_samples = 0
    if p50 is None or p50 <= 0:
        return _empty_pricing("insufficient_data", "数据不足", "low", "没有足够的同款市场价格，暂不生成自动定价。", current_price, market_samples, raw_samples, excluded_samples, risk_notes, is_gpu)
    p25, p35, p75 = p25 or p50, p35 or p25 or p50, p75 or p50
    price_band = {"p25": p25, "p35": p35, "p50": p50, "p75": p75}
    min_band_samples = GPU_MIN_BAND_SAMPLES if is_gpu else GENERIC_MIN_QUOTE_SAMPLES
    min_quote_samples = GPU_MIN_QUOTE_SAMPLES if is_gpu else GENERIC_MIN_QUOTE_SAMPLES
    if market_samples < min_band_samples:
        return _empty_pricing("insufficient_data", "数据不足", "low", f"有效同款样本仅 {market_samples} 条，少于最低参考门槛 {min_band_samples} 条。", current_price, market_samples, raw_samples, excluded_samples, risk_notes, is_gpu, price_band)
    if risk_notes and is_gpu:
        return _empty_pricing("risk_blocked", "风险拦截", "low", "检测到维修、矿卡或其他高风险信号，不把该商品当作正常卡自动报价。", current_price, market_samples, raw_samples, excluded_samples, risk_notes, is_gpu, price_band)
    if market_samples < min_quote_samples:
        return _empty_pricing("low_confidence", "参考区间", "low", f"同款有效样本 {market_samples} 条，仅展示价格区间；达到 {min_quote_samples} 条后才生成收货上限。", current_price, market_samples, raw_samples, excluded_samples, risk_notes, is_gpu, price_band)
    confidence = "high" if market_samples >= (GPU_HIGH_CONFIDENCE_SAMPLES if is_gpu else 10) else "medium"
    adjustment, signals = _condition_adjustment(record)
    suggested_listing = round(_clamp(p50 * (1 + adjustment), min(p25, p50), max(p50, p75)), 2)
    quick_sale = round(p35 * (1 + adjustment), 2)
    conservative = min(quick_sale, suggested_listing)
    platform_fee = round(conservative * PLATFORM_FEE_RATE, 2)
    inspection = round(conservative * INSPECTION_RESERVE_RATE, 2)
    after_sale = round(conservative * AFTER_SALE_RESERVE_RATE, 2)
    target_profit = round(max(MIN_TARGET_PROFIT, conservative * TARGET_MARGIN_RATE), 2)
    max_purchase = round(max(0.0, conservative - platform_fee - inspection - after_sale - LOGISTICS_RESERVE - target_profit), 2)
    expected_profit = expected_margin = gap = None
    if current_price is not None:
        expected_profit = round(conservative - current_price - platform_fee - inspection - after_sale - LOGISTICS_RESERVE, 2)
        expected_margin = round(expected_profit / conservative * 100, 2) if conservative else None
        gap = round(max_purchase - current_price, 2)
    can_buy = bool(current_price is not None and current_price <= max_purchase and expected_profit is not None and expected_profit >= MIN_TARGET_PROFIT and expected_margin is not None and expected_margin >= TARGET_MARGIN_RATE * 100)
    if can_buy:
        status, label = "priority_buy", "优先收货"
    elif current_price is not None and current_price <= max_purchase * 1.05:
        status, label = "negotiate", "可以谈价"
    else:
        status, label = "not_recommended", "不建议收货"
    reasons = [f"同款价格带 P25/P50/P75 为 ¥{p25:.0f}/¥{p50:.0f}/¥{p75:.0f}。", f"按 P35 快速出货价 ¥{quick_sale:.0f} 估算，保守变现价为 ¥{conservative:.0f}。", f"预留费用与准备金 ¥{platform_fee + inspection + after_sale + LOGISTICS_RESERVE:.0f}，目标利润 ¥{target_profit:.0f}。"]
    if signals:
        reasons.append("商品状态修正：" + "、".join(signals) + "。")
    if gap is not None:
        reasons.append(f"当前价较收货上限 {'高' if gap < 0 else '低'} ¥{abs(gap):.0f}。")
    return {
        "status": status, "label": label, "can_buy": can_buy, "confidence": confidence, "is_gpu": is_gpu,
        "market_sample_count": market_samples, "market_raw_sample_count": raw_samples, "market_excluded_sample_count": excluded_samples,
        "min_samples_for_quote": min_quote_samples, "price_band": price_band, "quick_sale_price": quick_sale,
        "conservative_resale_price": conservative, "suggested_listing_price": suggested_listing,
        "recommended_max_purchase_price": max_purchase, "expected_profit": expected_profit, "expected_margin": expected_margin,
        "state_adjustment_rate": adjustment, "state_adjustment_signals": signals,
        "cost_breakdown": {"platform_fee": platform_fee, "inspection_reserve": inspection, "after_sale_reserve": after_sale, "logistics_reserve": LOGISTICS_RESERVE, "target_profit": target_profit},
        "current_price": current_price, "gap_to_max_purchase_price": gap, "reasons": reasons, "risk_notes": risk_notes,
    }
