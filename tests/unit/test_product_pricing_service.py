from src.services.product_pricing_service import get_product_pricing


def test_product_pricing_has_the_agreed_entry_prices():
    catalog = get_product_pricing()
    plans = {plan["id"]: plan for plan in catalog["plans"]}

    assert plans["trial_7d"]["price"] == 9.9
    assert plans["personal_launch"]["price"] == 149
    assert plans["personal_annual"]["price"] == 199
    assert plans["personal_monthly"]["price"] == 29
    assert plans["professional_annual"]["price"] == 299
    assert plans["remote_setup"]["price"] == 69


def test_standard_personal_is_the_default_and_professional_is_not_sellable_yet():
    catalog = get_product_pricing()
    plans = {plan["id"]: plan for plan in catalog["plans"]}

    assert plans["personal_annual"]["recommended"] is True
    assert plans["personal_annual"]["availability"] == "available"
    assert plans["professional_annual"]["availability"] == "coming_soon"
    assert "不要按专业版收款" in plans["professional_annual"]["note"]["zh"]


def test_catalog_makes_api_and_delivery_boundaries_explicit():
    catalog = get_product_pricing()

    assert "API" in catalog["policies"]["api_cost"]["zh"]
    assert "人工确认订单" in catalog["policies"]["delivery"]["zh"]
    assert len(catalog["sales_guardrails"]) == 3
