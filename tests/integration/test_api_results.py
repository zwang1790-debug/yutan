import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import results
from src.services.price_history_service import record_market_snapshots


def _write_jsonl(path, records):
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def test_results_filter_and_sort_for_keyword_recommendations(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    target_file = jsonl_dir / "demo_full_data.jsonl"

    records = [
        {
            "爬取时间": "2026-01-01T01:00:00",
            "商品信息": {"当前售价": "¥1000", "发布时间": "2026-01-01 10:00"},
            "ai_analysis": {
                "analysis_source": "keyword",
                "is_recommended": True,
                "keyword_hit_count": 3,
                "reason": "命中 3 个关键词",
            },
        },
        {
            "爬取时间": "2026-01-01T02:00:00",
            "商品信息": {"当前售价": "¥2000", "发布时间": "2026-01-01 11:00"},
            "ai_analysis": {
                "analysis_source": "keyword",
                "is_recommended": True,
                "keyword_hit_count": 1,
                "reason": "命中 1 个关键词",
            },
        },
        {
            "爬取时间": "2026-01-01T03:00:00",
            "商品信息": {"当前售价": "¥3000", "发布时间": "2026-01-01 12:00"},
            "ai_analysis": {
                "analysis_source": "ai",
                "is_recommended": True,
                "reason": "AI推荐",
            },
        },
    ]
    _write_jsonl(target_file, records)

    app = FastAPI()
    app.include_router(results.router)
    client = TestClient(app)

    resp = client.get(
        "/api/results/demo_full_data.jsonl",
        params={"keyword_recommended_only": True, "sort_by": "keyword_hit_count", "sort_order": "desc"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_items"] == 2
    assert data["items"][0]["ai_analysis"]["keyword_hit_count"] == 3
    assert data["items"][1]["ai_analysis"]["keyword_hit_count"] == 1

    resp = client.get(
        "/api/results/demo_full_data.jsonl",
        params={"ai_recommended_only": True},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_items"] == 1
    assert data["items"][0]["ai_analysis"]["analysis_source"] == "ai"

    resp = client.get(
        "/api/results/demo_full_data.jsonl",
        params={"ai_recommended_only": True, "keyword_recommended_only": True},
    )
    assert resp.status_code == 400


def test_profit_estimate_can_be_saved_and_loaded_with_result(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    target_file = jsonl_dir / "demo_full_data.jsonl"
    _write_jsonl(
        target_file,
        [
            {
                "爬取时间": "2026-01-01T01:00:00",
                "商品信息": {
                    "商品ID": "1001",
                    "商品标题": "Demo One",
                    "商品链接": "https://www.goofish.com/item?id=1001",
                    "当前售价": "¥100",
                },
                "卖家信息": {},
                "ai_analysis": {"is_recommended": True},
            }
        ],
    )

    app = FastAPI()
    app.include_router(results.router)
    client = TestClient(app)

    save_resp = client.put(
        "/api/results/demo_full_data.jsonl/items/1001/profit-estimate",
        json={
            "purchase_price": 100,
            "resale_price": 180,
            "platform_fee": 5,
            "shipping_cost": 8,
            "other_cost": 2,
        },
    )
    assert save_resp.status_code == 200
    assert save_resp.json()["estimate"]["profit"] == 65

    list_resp = client.get("/api/results/demo_full_data.jsonl")
    assert list_resp.status_code == 200
    estimate = list_resp.json()["items"][0]["profit_estimate"]
    assert estimate["purchase_price"] == 100
    assert estimate["resale_price"] == 180

    missing_resp = client.put(
        "/api/results/demo_full_data.jsonl/items/missing/profit-estimate",
        json={"purchase_price": 1, "resale_price": 2},
    )
    assert missing_resp.status_code == 404


def test_inventory_record_can_be_saved_and_loaded_with_result(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    target_file = jsonl_dir / "demo_full_data.jsonl"
    _write_jsonl(
        target_file,
        [
            {
                "爬取时间": "2026-01-01T01:00:00",
                "商品信息": {
                    "商品ID": "1001",
                    "商品标题": "Demo One",
                    "商品链接": "https://www.goofish.com/item?id=1001",
                    "当前售价": "¥100",
                },
                "卖家信息": {},
                "ai_analysis": {"is_recommended": True},
            }
        ],
    )

    app = FastAPI()
    app.include_router(results.router)
    client = TestClient(app)

    save_resp = client.put(
        "/api/results/demo_full_data.jsonl/items/1001/inventory",
        json={
            "status": "sold",
            "actual_purchase_price": 100,
            "actual_sale_price": 180,
            "actual_platform_fee": 5,
            "actual_shipping_cost": 8,
        },
    )
    assert save_resp.status_code == 200
    assert save_resp.json()["record"]["actual_profit"] == 67

    list_resp = client.get("/api/results/demo_full_data.jsonl")
    assert list_resp.status_code == 200
    record = list_resp.json()["items"][0]["inventory_record"]
    assert record["status"] == "sold"
    assert record["actual_profit"] == 67


def test_results_insights_and_export_csv(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    target_file = jsonl_dir / "demo_full_data.jsonl"

    records = [
        {
            "爬取时间": "2026-01-02T09:00:00",
            "搜索关键字": "demo",
            "任务名称": "Demo 任务",
            "商品信息": {
                "商品ID": "1001",
                "商品标题": "Demo One",
                "商品链接": "https://www.goofish.com/item?id=1001",
                "当前售价": "¥950",
                "发布时间": "2026-01-02 08:30",
            },
            "卖家信息": {"卖家昵称": "卖家A"},
            "ai_analysis": {
                "analysis_source": "ai",
                "is_recommended": True,
                "reason": "价格低于近期均价",
            },
        },
        {
            "爬取时间": "2026-01-02T09:05:00",
            "搜索关键字": "demo",
            "任务名称": "Demo 任务",
            "商品信息": {
                "商品ID": "1002",
                "商品标题": "Demo Two",
                "商品链接": "https://www.goofish.com/item?id=1002",
                "当前售价": "¥1200",
                "发布时间": "2026-01-02 08:45",
            },
            "卖家信息": {"卖家昵称": "卖家B"},
            "ai_analysis": {
                "analysis_source": "keyword",
                "is_recommended": False,
                "reason": "未命中",
                "keyword_hit_count": 0,
            },
        },
    ]
    _write_jsonl(target_file, records)

    record_market_snapshots(
        keyword="demo",
        task_name="Demo 任务",
        items=[
            {
                "商品ID": "1001",
                "商品标题": "Demo One",
                "当前售价": "¥1000",
                "商品链接": "https://www.goofish.com/item?id=1001",
            },
            {
                "商品ID": "1002",
                "商品标题": "Demo Two",
                "当前售价": "¥1200",
                "商品链接": "https://www.goofish.com/item?id=1002",
            },
        ],
        run_id="run-1",
        snapshot_time="2026-01-01T10:00:00",
        seen_item_ids=set(),
    )
    record_market_snapshots(
        keyword="demo",
        task_name="Demo 任务",
        items=[
            {
                "商品ID": "1001",
                "商品标题": "Demo One",
                "当前售价": "¥950",
                "商品链接": "https://www.goofish.com/item?id=1001",
            },
            {
                "商品ID": "1002",
                "商品标题": "Demo Two",
                "当前售价": "¥1180",
                "商品链接": "https://www.goofish.com/item?id=1002",
            },
        ],
        run_id="run-2",
        snapshot_time="2026-01-02T10:00:00",
        seen_item_ids=set(),
    )

    app = FastAPI()
    app.include_router(results.router)
    client = TestClient(app)

    insights_resp = client.get("/api/results/demo_full_data.jsonl/insights")
    assert insights_resp.status_code == 200
    insights = insights_resp.json()
    assert insights["market_summary"]["sample_count"] == 2
    assert len(insights["daily_trend"]) == 2

    list_resp = client.get("/api/results/demo_full_data.jsonl")
    assert list_resp.status_code == 200
    items = list_resp.json()["items"]
    assert items[0]["price_insight"]["observation_count"] >= 1

    export_resp = client.get(
        "/api/results/demo_full_data.jsonl/export",
        params={"sort_by": "price", "sort_order": "asc"},
    )
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["content-type"]
    text = export_resp.text
    assert "任务名称,搜索关键字,商品ID,商品标题" in text
    assert "Demo One" in text


def test_results_export_csv_supports_unicode_filename(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    target_file = jsonl_dir / "演示_full_data.jsonl"

    records = [
        {
            "爬取时间": "2026-01-02T09:00:00",
            "搜索关键字": "演示",
            "任务名称": "演示任务",
            "商品信息": {
                "商品ID": "1001",
                "商品标题": "演示商品",
                "商品链接": "https://www.goofish.com/item?id=1001",
                "当前售价": "¥950",
                "发布时间": "2026-01-02 08:30",
            },
            "卖家信息": {"卖家昵称": "卖家A"},
            "ai_analysis": {
                "analysis_source": "ai",
                "is_recommended": True,
                "reason": "价格合理",
            },
        }
    ]
    _write_jsonl(target_file, records)

    app = FastAPI()
    app.include_router(results.router)
    client = TestClient(app)

    export_resp = client.get("/api/results/演示_full_data.jsonl/export")
    assert export_resp.status_code == 200
    assert "text/csv" in export_resp.headers["content-type"]
    disposition = export_resp.headers["content-disposition"]
    assert 'filename="export.csv"' in disposition
    assert "filename*=UTF-8''%E6%BC%94%E7%A4%BA_full_data.csv" in disposition


def test_results_can_sort_and_export_explainable_opportunities(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    target_file = jsonl_dir / "gpu_full_data.jsonl"
    _write_jsonl(
        target_file,
        [
            {
                "爬取时间": "2026-01-03T10:00:00",
                "搜索关键字": "gpu",
                "商品信息": {
                    "商品ID": "3001",
                    "商品标题": "RTX 4060 Ti 8G 个人自用",
                    "商品链接": "https://www.goofish.com/item?id=3001",
                    "当前售价": "¥1800",
                },
                "ai_analysis": {"is_recommended": True, "reason": "低于市场"},
            },
            {
                "爬取时间": "2026-01-03T10:01:00",
                "搜索关键字": "gpu",
                "商品信息": {
                    "商品ID": "3002",
                    "商品标题": "RTX 4060 Ti 8GB 拆机",
                    "商品链接": "https://www.goofish.com/item?id=3002",
                    "当前售价": "¥2750",
                },
                "ai_analysis": {"is_recommended": True, "reason": "价格较高"},
            },
            *[
                {
                    "爬取时间": "2026-01-03T10:02:00",
                    "搜索关键字": "gpu",
                    "商品信息": {
                        "商品ID": f"reference-{index}",
                        "商品标题": "RTX 4060 Ti 8G 个人自用",
                        "商品链接": f"https://www.goofish.com/item?id=reference-{index}",
                        "当前售价": f"¥{price}",
                    },
                    "ai_analysis": {"is_recommended": False, "reason": "市场参考"},
                }
                for index, price in enumerate([2400, 2500, 2600, 2700, 2800], start=1)
            ],
        ],
    )
    record_market_snapshots(
        keyword="gpu",
        task_name="GPU 监控",
        items=[
            {"商品ID": "3001", "商品标题": "RTX 4060 Ti 8G", "当前售价": "¥2000", "商品链接": "https://www.goofish.com/item?id=3001"},
            {"商品ID": "3002", "商品标题": "RTX 4060 Ti 8GB", "当前售价": "¥2700", "商品链接": "https://www.goofish.com/item?id=3002"},
            *[
                {"商品ID": f"reference-{index}", "商品标题": "RTX 4060 Ti 8G", "当前售价": f"¥{price}", "商品链接": f"https://www.goofish.com/item?id=reference-{index}"}
                for index, price in enumerate([2400, 2500, 2600, 2700, 2800], start=1)
            ],
        ],
        run_id="run-1",
        snapshot_time="2026-01-03T10:05:00",
        seen_item_ids=set(),
    )

    app = FastAPI()
    app.include_router(results.router)
    client = TestClient(app)

    response = client.get(
        "/api/results/gpu_full_data.jsonl",
        params={"sort_by": "opportunity_score", "sort_order": "desc"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    items_by_id = {item["商品信息"]["商品ID"]: item for item in items}
    assert items[0]["商品信息"]["商品ID"] == "3001"
    assert items_by_id["3001"]["opportunity_assessment"]["score"] is not None
    assert items_by_id["3002"]["opportunity_assessment"]["score"] is None
    assert items_by_id["3001"]["opportunity_assessment"]["recommended_max_purchase_price"] is not None
    assert "拆机" in items_by_id["3002"]["opportunity_assessment"]["risk_notes"]

    export_response = client.get(
        "/api/results/gpu_full_data.jsonl/export",
        params={"sort_by": "opportunity_score", "sort_order": "desc"},
    )
    assert export_response.status_code == 200
    assert "机会分" in export_response.text
    assert "建议最高收货价" in export_response.text


def test_result_insights_include_business_summary(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    target_file = jsonl_dir / "phone_full_data.jsonl"
    _write_jsonl(
        target_file,
        [
            {
                "爬取时间": "2026-01-03T10:00:00",
                "搜索关键字": "phone",
                "商品信息": {
                    "商品ID": "4001",
                    "商品标题": "iPhone 15 Pro 256GB",
                    "商品链接": "https://www.goofish.com/item?id=4001",
                    "当前售价": "¥3000",
                },
                "卖家信息": {},
                "ai_analysis": {"is_recommended": True},
            }
        ],
    )
    app = FastAPI()
    app.include_router(results.router)
    client = TestClient(app)

    save_response = client.put(
        "/api/results/phone_full_data.jsonl/items/4001/inventory",
        json={
            "status": "sold",
            "actual_purchase_price": 2500,
            "actual_sale_price": 3000,
            "actual_platform_fee": 30,
        },
    )
    assert save_response.status_code == 200

    insights_response = client.get("/api/results/phone_full_data.jsonl/insights")
    assert insights_response.status_code == 200
    summary = insights_response.json()["business_summary"]
    assert summary["tracked_items"] == 1
    assert summary["realized_profit"] == 470
    assert summary["status_counts"]["sold"] == 1


def test_results_blacklist_rules_hide_items_from_view_and_insights(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    jsonl_dir = tmp_path / "jsonl"
    jsonl_dir.mkdir(parents=True, exist_ok=True)
    target_file = jsonl_dir / "macbook_air_m1_full_data.jsonl"

    records = [
        {
            "爬取时间": "2026-01-03T09:00:00",
            "搜索关键字": "MacBook Air M1",
            "任务名称": "MacBook Air M1 监控",
            "商品信息": {
                "商品ID": "2001",
                "商品标题": "MacBook Air M1 8+256",
                "商品链接": "https://www.goofish.com/item?id=2001",
                "当前售价": "¥4200",
                "发布时间": "2026-01-03 08:30",
            },
            "卖家信息": {"卖家昵称": "卖家A"},
            "ai_analysis": {
                "analysis_source": "ai",
                "is_recommended": True,
                "reason": "符合目标机型",
            },
        },
        {
            "爬取时间": "2026-01-03T09:05:00",
            "搜索关键字": "MacBook Air M1",
            "任务名称": "MacBook Air M1 监控",
            "商品信息": {
                "商品ID": "2002",
                "商品标题": "MacBook Air Intel i5 8+256",
                "商品链接": "https://www.goofish.com/item?id=2002",
                "当前售价": "¥3100",
                "发布时间": "2026-01-03 08:35",
            },
            "卖家信息": {"卖家昵称": "卖家B"},
            "ai_analysis": {
                "analysis_source": "ai",
                "is_recommended": False,
                "reason": "不是目标机型",
            },
        },
        {
            "爬取时间": "2026-01-03T09:10:00",
            "搜索关键字": "MacBook Air M1",
            "任务名称": "MacBook Air M1 监控",
            "商品信息": {
                "商品ID": "2003",
                "商品标题": "MacBook Pro Intel 13寸",
                "商品链接": "https://www.goofish.com/item?id=2003",
                "当前售价": "¥3600",
                "发布时间": "2026-01-03 08:40",
            },
            "卖家信息": {"卖家昵称": "卖家C"},
            "ai_analysis": {
                "analysis_source": "ai",
                "is_recommended": False,
                "reason": "不是 Air M1",
            },
        },
    ]
    _write_jsonl(target_file, records)

    record_market_snapshots(
        keyword="MacBook Air M1",
        task_name="MacBook Air M1 监控",
        items=[
            {
                "商品ID": "2001",
                "商品标题": "MacBook Air M1 8+256",
                "当前售价": "¥4300",
                "商品链接": "https://www.goofish.com/item?id=2001",
            },
            {
                "商品ID": "2002",
                "商品标题": "MacBook Air Intel i5 8+256",
                "当前售价": "¥3200",
                "商品链接": "https://www.goofish.com/item?id=2002",
            },
            {
                "商品ID": "2003",
                "商品标题": "MacBook Pro Intel 13寸",
                "当前售价": "¥3700",
                "商品链接": "https://www.goofish.com/item?id=2003",
            },
        ],
        run_id="run-1",
        snapshot_time="2026-01-02T10:00:00",
        seen_item_ids=set(),
    )
    record_market_snapshots(
        keyword="MacBook Air M1",
        task_name="MacBook Air M1 监控",
        items=[
            {
                "商品ID": "2001",
                "商品标题": "MacBook Air M1 8+256",
                "当前售价": "¥4200",
                "商品链接": "https://www.goofish.com/item?id=2001",
            },
            {
                "商品ID": "2002",
                "商品标题": "MacBook Air Intel i5 8+256",
                "当前售价": "¥3100",
                "商品链接": "https://www.goofish.com/item?id=2002",
            },
            {
                "商品ID": "2003",
                "商品标题": "MacBook Pro Intel 13寸",
                "当前售价": "¥3600",
                "商品链接": "https://www.goofish.com/item?id=2003",
            },
        ],
        run_id="run-2",
        snapshot_time="2026-01-03T10:00:00",
        seen_item_ids=set(),
    )

    app = FastAPI()
    app.include_router(results.router)
    client = TestClient(app)

    update_rules_resp = client.put(
        "/api/results/macbook_air_m1_full_data.jsonl/blacklist-rules",
        json={"keywords": ["intel"]},
    )
    assert update_rules_resp.status_code == 200
    assert update_rules_resp.json()["keywords"] == ["intel"]

    rules_resp = client.get("/api/results/macbook_air_m1_full_data.jsonl/blacklist-rules")
    assert rules_resp.status_code == 200
    assert rules_resp.json()["keywords"] == ["intel"]

    filtered_resp = client.get("/api/results/macbook_air_m1_full_data.jsonl")
    assert filtered_resp.status_code == 200
    filtered_payload = filtered_resp.json()
    assert filtered_payload["total_items"] == 1
    assert [item["商品信息"]["商品ID"] for item in filtered_payload["items"]] == ["2001"]

    include_hidden_resp = client.get(
        "/api/results/macbook_air_m1_full_data.jsonl",
        params={"include_hidden": True},
    )
    assert include_hidden_resp.status_code == 200
    include_hidden_payload = include_hidden_resp.json()
    assert include_hidden_payload["total_items"] == 3
    hidden_item = next(
        item for item in include_hidden_payload["items"]
        if item["商品信息"]["商品ID"] == "2002"
    )
    assert hidden_item["_hidden_reason"] == "rule"
    assert hidden_item["_matched_blacklist_keywords"] == ["intel"]

    insights_resp = client.get("/api/results/macbook_air_m1_full_data.jsonl/insights")
    assert insights_resp.status_code == 200
    insights = insights_resp.json()
    assert insights["market_summary"]["sample_count"] == 1
    assert insights["market_summary"]["avg_price"] == 4200.0
    assert all(point["sample_count"] == 1 for point in insights["daily_trend"])

    list_resp = client.get("/api/results/macbook_air_m1_full_data.jsonl")
    assert list_resp.status_code == 200
    visible_item = list_resp.json()["items"][0]
    assert visible_item["price_insight"]["market_avg_price"] == 4200.0

    export_resp = client.get("/api/results/macbook_air_m1_full_data.jsonl/export")
    assert export_resp.status_code == 200
    assert "MacBook Air M1 8+256" in export_resp.text
    assert "MacBook Air Intel i5 8+256" not in export_resp.text
    assert "MacBook Pro Intel 13寸" not in export_resp.text

    download_resp = client.get("/api/results/files/macbook_air_m1_full_data.jsonl")
    assert download_resp.status_code == 200
    assert "MacBook Air Intel i5 8+256" in download_resp.text
    assert "MacBook Pro Intel 13寸" in download_resp.text
