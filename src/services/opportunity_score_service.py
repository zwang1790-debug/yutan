"""Explainable resale opportunity scoring for result listings."""
from __future__ import annotations

import math
from typing import Any

DEFAULT_PLATFORM_FEE_RATE = 0.05
TARGET_MARGIN_RATE = 0.12
GPU_INSPECTION_RESERVE_RATE = 0.03
GPU_LOGISTICS_RESERVE = 30.0
RISK_KEYWORDS = ("维修", "拆机", "暗病", "故障", "进水", "锁机", "监管机", "租赁", "翻新", "配件机")


def _number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return round(number, 2) if math.isfinite(number) else None


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _risk_notes(record: dict) -> list[str]:
    analysis = record.get("ai_analysis", {}) or {}
    tags = [str(tag).strip() for tag in (analysis.get("risk_tags") or []) if str(tag).strip()]
    title = str((record.get("商品信息", {}) or {}).get("商品标题") or "").lower()
    for keyword in RISK_KEYWORDS:
        if keyword in title and keyword not in tags:
            tags.append(keyword)
    return tags[:4]


def _resolve_label(score: int | None) -> str:
    if score is None:
        return "数据不足"
    if score >= 75:
        return "优先联系"
    if score >= 55:
        return "可谈价"
    if score >= 35:
        return "继续观察"
    return "谨慎评估"


def build_opportunity_assessment(record: dict, price_insight: dict | None) -> dict:
    """Turn market reference and listing signals into an auditable resale decision."""
    insight = price_insight or {}
    current_price = _number(insight.get("current_price"))
    resale_price = _number(insight.get("market_median_price")) or _number(insight.get("market_avg_price"))
    conservative_resale_price = _number(insight.get("market_p25_price")) or resale_price
    try:
        market_samples = max(0, int(insight.get("market_sample_count") or 0))
    except (TypeError, ValueError):
        market_samples = 0
    risk_notes = _risk_notes(record)
    if current_price is None or resale_price is None or resale_price <= 0:
        return {
            "score": None, "label": _resolve_label(None), "confidence": "low",
            "suggested_listing_price": resale_price, "recommended_max_purchase_price": None,
            "expected_profit": None, "expected_margin": None, "market_sample_count": market_samples,
            "price_discount_percent": None, "components": {},
            "reasons": ["有效同款样本不足，暂不建议按机会分决策。"], "risk_notes": risk_notes,
        }

    platform_fee_reserve = round(resale_price * DEFAULT_PLATFORM_FEE_RATE, 2)
    is_gpu_valuation = _number(insight.get("market_p25_price")) is not None
    if is_gpu_valuation and risk_notes:
        return {
            "score": None, "label": "风险拦截", "confidence": "low",
            "suggested_listing_price": resale_price, "recommended_max_purchase_price": None,
            "expected_profit": None, "expected_margin": None, "market_sample_count": market_samples,
            "price_discount_percent": None, "components": {},
            "reasons": ["该显卡含高风险信号，已停止自动报价，请人工核验后再决定。"],
            "risk_notes": risk_notes,
        }
    inspection_reserve = round(resale_price * GPU_INSPECTION_RESERVE_RATE, 2) if is_gpu_valuation else 0.0
    logistics_reserve = GPU_LOGISTICS_RESERVE if is_gpu_valuation else 0.0
    target_profit_reserve = round(conservative_resale_price * TARGET_MARGIN_RATE, 2)
    max_purchase_price = round(max(0, conservative_resale_price - platform_fee_reserve - inspection_reserve - logistics_reserve - target_profit_reserve), 2)
    expected_profit = round(conservative_resale_price - current_price - platform_fee_reserve - inspection_reserve - logistics_reserve, 2)
    expected_margin = round(expected_profit / conservative_resale_price * 100, 2)
    price_discount_percent = round((resale_price - current_price) / resale_price * 100, 2)
    profit_space = round(_clamp(expected_margin / 25 * 50, 0, 50), 1)
    price_position = round(_clamp(price_discount_percent / 20 * 20, 0, 20), 1)
    liquidity = round(_clamp(market_samples / 8 * 15, 0, 15), 1)
    analysis = record.get("ai_analysis", {}) or {}
    recommendation = 15.0 if analysis.get("is_recommended") else 0.0
    if not analysis.get("is_recommended") and int(analysis.get("keyword_hit_count") or 0) > 0:
        recommendation = 6.0
    risk_deduction = min(20.0, len(risk_notes) * 5.0)
    confidence = "high" if market_samples >= 5 else "medium" if market_samples >= 2 else "low"
    if confidence == "low":
        risk_deduction += 8.0
    score = int(round(_clamp(profit_space + price_position + liquidity + recommendation - risk_deduction, 0, 100)))
    confidence_label = {"high": "高", "medium": "中", "low": "低"}[confidence]
    reasons = [
        f"按同款参考价 ¥{resale_price:.0f} 估算，保守变现价 ¥{conservative_resale_price:.0f}，预计利润 ¥{expected_profit:.0f}。",
        f"当前价较同款参考价 {'低' if price_discount_percent >= 0 else '高'} {abs(price_discount_percent):.1f}%。",
        f"同款参考样本 {market_samples} 条，置信度{confidence_label}。",
    ]
    if risk_notes:
        reasons.append("风险信号：" + "、".join(risk_notes) + "。")
    return {
        "score": score, "label": _resolve_label(score), "confidence": confidence,
        "suggested_listing_price": resale_price, "recommended_max_purchase_price": max_purchase_price,
        "expected_profit": expected_profit, "expected_margin": expected_margin,
        "market_sample_count": market_samples, "price_discount_percent": price_discount_percent,
        "components": {"profit_space": profit_space, "price_position": price_position, "liquidity": liquidity, "recommendation": recommendation, "risk_deduction": risk_deduction},
        "reasons": reasons, "risk_notes": risk_notes,
    }


def sort_records_by_opportunity(records: list[dict], sort_order: str = "desc") -> list[dict]:
    def key(record: dict) -> tuple[int, int]:
        score = (record.get("opportunity_assessment", {}) or {}).get("score")
        if score is None:
            return (1, 0)
        return (0, -int(score) if sort_order != "asc" else int(score))

    return sorted(records, key=key)
