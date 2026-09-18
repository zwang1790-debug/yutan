import pytest

from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.infrastructure.persistence.sqlite_connection import sqlite_connection
from src.services.inventory_service import load_inventory_records, save_inventory_record


def _insert_result_item():
    with sqlite_connection() as conn:
        conn.execute(
            """
            INSERT INTO result_items (
                result_filename, keyword, task_name, crawl_time, item_id,
                link_unique_key, is_recommended, keyword_hit_count, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "demo_full_data.jsonl",
                "demo",
                "Demo",
                "2026-01-01T00:00:00",
                "1001",
                "item:1001",
                1,
                0,
                "{}",
            ),
        )
        conn.commit()


def test_inventory_status_and_actual_profit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bootstrap_sqlite_storage()
    _insert_result_item()

    saved = save_inventory_record(
        "demo_full_data.jsonl",
        "1001",
        {
            "status": "purchased",
            "actual_purchase_price": 100,
            "actual_platform_fee": 5,
            "actual_shipping_cost": 8,
        },
    )
    assert saved["actual_profit"] is None
    assert saved["purchased_at"]

    sold = save_inventory_record(
        "demo_full_data.jsonl",
        "1001",
        {"status": "sold", "actual_sale_price": 180},
    )
    assert sold["actual_profit"] == 67
    assert sold["actual_margin"] == round(67 / 180 * 100, 2)
    assert sold["purchased_at"]
    assert sold["sold_at"]

    loaded = load_inventory_records("demo_full_data.jsonl")["1001"]
    assert loaded["status"] == "sold"
    assert loaded["actual_profit"] == 67


def test_inventory_rejects_invalid_status_and_amount(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bootstrap_sqlite_storage()
    _insert_result_item()

    with pytest.raises(ValueError, match="状态"):
        save_inventory_record("demo_full_data.jsonl", "1001", {"status": "unknown"})
    with pytest.raises(ValueError, match="不能小于 0"):
        save_inventory_record(
            "demo_full_data.jsonl",
            "1001",
            {"status": "purchased", "actual_purchase_price": -1},
        )
