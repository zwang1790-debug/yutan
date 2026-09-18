from src.services.price_history_service import (
    build_item_price_context,
    build_price_history_insights,
    build_gpu_market_valuation,
    load_price_snapshots,
    normalize_model_key,
    record_market_snapshots,
)


def test_record_market_snapshots_and_build_price_history_insights(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    seen_item_ids = set()

    run1_items = [
        {
            "商品ID": "1001",
            "商品标题": "Sony A7M4 单机",
            "当前售价": "¥10000",
            "商品标签": ["验货宝"],
            "发货地区": "上海",
            "卖家昵称": "卖家A",
            "商品链接": "https://www.goofish.com/item?id=1001",
            "发布时间": "2026-01-01 09:00",
        },
        {
            "商品ID": "1002",
            "商品标题": "Sony A7M4 套机",
            "当前售价": "¥12000",
            "商品标签": ["包邮"],
            "发货地区": "杭州",
            "卖家昵称": "卖家B",
            "商品链接": "https://www.goofish.com/item?id=1002",
            "发布时间": "2026-01-01 10:00",
        },
    ]
    run2_items = [
        {
            "商品ID": "1001",
            "商品标题": "Sony A7M4 单机",
            "当前售价": "¥9500",
            "商品标签": ["验货宝"],
            "发货地区": "上海",
            "卖家昵称": "卖家A",
            "商品链接": "https://www.goofish.com/item?id=1001",
            "发布时间": "2026-01-02 09:00",
        },
        {
            "商品ID": "1003",
            "商品标题": "Sony A7M4 全套",
            "当前售价": "¥13000",
            "商品标签": ["同城"],
            "发货地区": "南京",
            "卖家昵称": "卖家C",
            "商品链接": "https://www.goofish.com/item?id=1003",
            "发布时间": "2026-01-02 11:00",
        },
    ]

    inserted_run1 = record_market_snapshots(
        keyword="sony a7m4",
        task_name="Sony A7M4 监控",
        items=run1_items,
        run_id="run-1",
        snapshot_time="2026-01-01T12:00:00",
        seen_item_ids=seen_item_ids,
    )
    assert len(inserted_run1) == 2

    inserted_run2 = record_market_snapshots(
        keyword="sony a7m4",
        task_name="Sony A7M4 监控",
        items=run2_items,
        run_id="run-2",
        snapshot_time="2026-01-02T12:00:00",
        seen_item_ids=set(),
    )
    assert len(inserted_run2) == 2

    snapshots = load_price_snapshots("sony a7m4")
    assert len(snapshots) == 4

    insights = build_price_history_insights("sony a7m4")
    assert insights["market_summary"]["sample_count"] == 2
    assert insights["market_summary"]["avg_price"] == 11250.0
    assert insights["market_summary"]["min_price"] == 9500.0
    assert insights["history_summary"]["unique_items"] == 3
    assert len(insights["daily_trend"]) == 2
    assert insights["daily_trend"][0]["day"] == "2026-01-01"
    assert insights["daily_trend"][1]["day"] == "2026-01-02"

    item_context = build_item_price_context(
        snapshots,
        item_id="1001",
        current_price=9500.0,
    )
    assert item_context["observation_count"] == 2
    assert item_context["min_price"] == 9500.0
    assert item_context["max_price"] == 10000.0
    assert item_context["price_change_amount"] == -500.0
    assert item_context["deal_label"] == "高性价比"


def test_normalize_model_key_preserves_material_hardware_variants():
    assert normalize_model_key("七彩虹 RTX 4060 Ti 8GB") == "rtx 4060 ti 8g"
    assert normalize_model_key("MacBook Air M1 8+256 国行") == "macbook air m1 8g 256g"
    assert normalize_model_key("iPhone 15 Pro Max 256GB") == "iphone 15 promax 256g"


def test_gpu_listing_with_too_few_comparables_does_not_receive_buy_quote():
    market_snapshots = [
        {
            "run_id": "run-1",
            "item_id": "market-1",
            "title": "RTX 4060 Ti 8G",
            "price": 2600,
            "snapshot_time": "2026-01-03T10:00:00",
        },
        {
            "run_id": "run-1",
            "item_id": "market-2",
            "title": "RTX 4060 Ti 8GB",
            "price": 2800,
            "snapshot_time": "2026-01-03T10:00:00",
        },
    ]

    context = build_item_price_context(
        market_snapshots,
        item_id="new-listing",
        current_price=2000,
        item_title="RTX 4060 Ti 8G",
        market_snapshots=market_snapshots,
    )

    assert context["observation_count"] == 0
    assert context["current_price"] == 2000
    assert context["market_median_price"] is None
    assert context["market_sample_count"] == 2
    assert context["deal_score"] == 50
    assert context["market_valuation_eligible"] is False


def test_gpu_valuation_filters_risky_and_extreme_listings_before_pricing():
    snapshots = [
        {
            "run_id": "run-1", "item_id": f"safe-{index}", "title": "RTX 4060 Ti 8G",
            "price": price, "snapshot_time": "2026-01-03T10:00:00",
        }
        for index, price in enumerate([2500, 2600, 2700, 2800, 2900], start=1)
    ]
    snapshots.extend([
        {
            "run_id": "run-1", "item_id": "risky", "title": "RTX 4060 Ti 8G 矿卡拆机",
            "price": 1500, "snapshot_time": "2026-01-03T10:00:00",
        },
        {
            "run_id": "run-1", "item_id": "outlier", "title": "RTX 4060 Ti 8G",
            "price": 9999, "snapshot_time": "2026-01-03T10:00:00",
        },
    ])

    valuation = build_gpu_market_valuation(snapshots, "rtx 4060 ti 8g")

    assert valuation["is_eligible"] is True
    assert valuation["sample_count"] == 5
    assert valuation["excluded_sample_count"] == 2
    assert valuation["p25_price"] == 2600
    assert valuation["p50_price"] == 2700
    assert valuation["p75_price"] == 2800
