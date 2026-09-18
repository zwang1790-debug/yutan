from src.services.pricing_service import build_pricing_assessment


def _record(title="RTX 4060 Ti 8G 个人自用"):
    return {
        "商品信息": {"商品标题": title, "当前售价": "1800"},
        "ai_analysis": {"risk_tags": []},
    }


def _insight(samples=12):
    return {
        "current_price": 1800,
        "market_model_key": "rtx 4060 ti 8g",
        "market_sample_count": samples,
        "market_raw_sample_count": samples + 2,
        "market_excluded_sample_count": 2,
        "market_p25_price": 2300,
        "market_p35_price": 2400,
        "market_p50_price": 2600,
        "market_p75_price": 2900,
    }


def test_pricing_assessment_outputs_conservative_prices_and_buy_decision():
    result = build_pricing_assessment(_record(), _insight())

    assert result["status"] == "priority_buy"
    assert result["can_buy"] is True
    assert result["price_band"] == {"p25": 2300, "p35": 2400, "p50": 2600, "p75": 2900}
    assert result["quick_sale_price"] == 2448
    assert result["suggested_listing_price"] == 2652
    assert result["recommended_max_purchase_price"] == 1854.96
    assert result["expected_profit"] == 348.72
    assert result["cost_breakdown"] == {
        "platform_fee": 122.4,
        "inspection_reserve": 73.44,
        "after_sale_reserve": 73.44,
        "logistics_reserve": 30.0,
        "target_profit": 293.76,
    }


def test_pricing_assessment_refuses_quote_for_gpu_with_few_samples():
    result = build_pricing_assessment(_record(), _insight(samples=5))

    assert result["status"] == "low_confidence"
    assert result["can_buy"] is False
    assert result["recommended_max_purchase_price"] is None
    assert result["price_band"]["p50"] == 2600


def test_pricing_assessment_respects_negated_risk_phrases():
    clean = build_pricing_assessment(_record("RTX 4060 Ti 8G 非矿卡 无拆无修 自用拆机出"), _insight())
    risky = build_pricing_assessment(_record("RTX 4060 Ti 8G 矿卡维修"), _insight())

    assert clean["status"] == "priority_buy"
    assert "矿卡" not in clean["risk_notes"]
    assert risky["status"] == "risk_blocked"
    assert risky["can_buy"] is False
