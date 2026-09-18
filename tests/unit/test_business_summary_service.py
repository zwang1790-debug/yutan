from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.infrastructure.persistence.sqlite_connection import sqlite_connection
from src.services.business_summary_service import load_result_business_summary


def _insert_result_item(item_id: str, title: str) -> None:
    with sqlite_connection() as conn:
        conn.execute(
            """
            INSERT INTO result_items (
                result_filename, keyword, task_name, crawl_time, item_id, title,
                link_unique_key, is_recommended, keyword_hit_count, raw_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "camera_full_data.jsonl",
                "camera",
                "Camera",
                "2026-01-03T00:00:00",
                item_id,
                title,
                f"item:{item_id}",
                1,
                0,
                "{}",
            ),
        )
        conn.commit()


def _insert_inventory(
    item_id: str,
    status: str,
    purchase_price: float | None,
    sale_price: float | None,
    *,
    purchased_at: str | None = None,
    sold_at: str | None = None,
) -> None:
    with sqlite_connection() as conn:
        conn.execute(
            """
            INSERT INTO inventory_records (
                result_filename, item_id, status, actual_purchase_price,
                actual_sale_price, actual_platform_fee, actual_shipping_cost,
                actual_other_cost, notes, purchased_at, listed_at, sold_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "camera_full_data.jsonl",
                item_id,
                status,
                purchase_price,
                sale_price,
                5,
                8,
                2,
                "",
                purchased_at,
                None,
                sold_at,
                "2026-01-03T00:00:00",
            ),
        )
        conn.commit()


def test_business_summary_separates_realized_profit_and_open_inventory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    bootstrap_sqlite_storage()
    _insert_result_item("1", "Sony A7M4 单机")
    _insert_result_item("2", "Sony A7M4 单机")
    _insert_result_item("3", "Sony A7M4 单机")
    _insert_inventory(
        "1",
        "sold",
        100,
        180,
        purchased_at="2026-01-01T00:00:00",
        sold_at="2026-01-03T00:00:00",
    )
    _insert_inventory("2", "listed", 200, None)
    _insert_inventory("3", "sold", 90, None)

    summary = __import__(
        "asyncio"
    ).run(load_result_business_summary("camera_full_data.jsonl"))

    assert summary["tracked_items"] == 3
    assert summary["status_counts"]["sold"] == 2
    assert summary["owned_items"] == 3
    assert summary["open_inventory_items"] == 1
    assert summary["open_inventory_cost"] == 200.0
    assert summary["realized_profit"] == 65.0
    assert summary["realized_roi"] == 65.0
    assert summary["sold_items"] == 2
    assert summary["incomplete_sold_items"] == 1
    assert summary["average_turnover_days"] == 2.0
    assert summary["turnover_sample_count"] == 1
    assert summary["model_performance"][0]["model_key"] == "sony a7m4"
