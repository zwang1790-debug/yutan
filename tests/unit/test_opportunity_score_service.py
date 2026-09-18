from src.services.opportunity_score_service import (
    build_opportunity_assessment,
    sort_records_by_opportunity,
)


def _record(*, recommended=True, title="RTX 4060 Ti 8G"):
    return {
        "商品信息": {"商品标题": title},
        "ai_analysis": {"is_recommended": recommended, "risk_tags": []},
    }


def test_opportunity_assessment_explains_profit_and_risk():
    assessment = build_opportunity_assessment(
        _record(),
        {
            "current_price": 2000,
            "market_median_price": 2800,
            "market_sample_count": 6,
        },
    )

    assert assessment["score"] >= 75
    assert assessment["label"] == "优先联系"
    assert assessment["recommended_max_purchase_price"] == 2324
    assert assessment["expected_profit"] == 660
    assert assessment["confidence"] == "high"

    risky = build_opportunity_assessment(
        _record(title="RTX 4060 Ti 8G 拆机维修"),
        {"current_price": 2000, "market_median_price": 2800, "market_sample_count": 6},
    )
    assert "拆机" in risky["risk_notes"]
    assert risky["score"] < assessment["score"]


def test_opportunity_score_requires_market_reference_and_keeps_unknown_last():
    unavailable = build_opportunity_assessment(_record(), None)
    assert unavailable["score"] is None

    records = [
        {"opportunity_assessment": {"score": None}},
        {"opportunity_assessment": {"score": 40}},
        {"opportunity_assessment": {"score": 82}},
    ]
    assert [item["opportunity_assessment"]["score"] for item in sort_records_by_opportunity(records)] == [82, 40, None]
    assert [item["opportunity_assessment"]["score"] for item in sort_records_by_opportunity(records, "asc")] == [40, 82, None]


def test_gpu_risk_signal_blocks_automatic_purchase_quote():
    assessment = build_opportunity_assessment(
        _record(title="RTX 4060 Ti 8G 拆机维修"),
        {
            "current_price": 1800,
            "market_median_price": 2600,
            "market_p25_price": 2400,
            "market_sample_count": 8,
        },
    )

    assert assessment["score"] is None
    assert assessment["label"] == "风险拦截"
    assert assessment["recommended_max_purchase_price"] is None


def test_opportunity_assessment_tolerates_invalid_market_sample_count():
    assessment = build_opportunity_assessment(
        _record(),
        {"current_price": 2000, "market_median_price": 2800, "market_sample_count": "unknown"},
    )

    assert assessment["market_sample_count"] == 0
    assert assessment["confidence"] == "low"
