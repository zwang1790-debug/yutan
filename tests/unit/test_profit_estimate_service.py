import pytest

from src.services.profit_estimate_service import (
    calculate_profit,
    load_profit_estimates,
    save_profit_estimate,
)
from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.infrastructure.persistence.sqlite_connection import sqlite_connection


def test_calculate_profit_and_reject_invalid_amounts():
    result = calculate_profit(
        {
            "purchase_price": 100,
            "resale_price": 180,
            "platform_fee": 5,
            "shipping_cost": 8,
            "other_cost": 2,
        }
    )
    assert result["profit"] == 65
    assert result["margin"] == round(65 / 180 * 100, 2)

    with pytest.raises(ValueError, match="不能小于 0"):
        calculate_profit({"purchase_price": -1, "resale_price": 10})


def test_save_and_load_profit_estimate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bootstrap_sqlite_storage()
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

    saved = save_profit_estimate(
        "demo_full_data.jsonl",
        "1001",
        {"purchase_price": 100, "resale_price": 180, "platform_fee": 5},
    )
    assert saved["purchase_price"] == 100
    assert load_profit_estimates("demo_full_data.jsonl")["1001"]["resale_price"] == 180

    updated = save_profit_estimate(
        "demo_full_data.jsonl",
        "1001",
        {"purchase_price": 110, "resale_price": 200},
    )
    assert updated["purchase_price"] == 110
    assert load_profit_estimates("demo_full_data.jsonl")["1001"]["platform_fee"] == 0
