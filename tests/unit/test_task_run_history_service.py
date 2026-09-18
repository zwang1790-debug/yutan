from src.services import task_run_history_service as service


def test_task_history_records_success_and_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "HISTORY_PATH", tmp_path / "history.json")
    service.record_start(1, "测试任务")
    service.record_finish(1, 0)
    service.record_start(1, "测试任务")
    service.record_finish(1, 1)

    result = service.get_task_history(1)
    assert result["total_runs"] == 2
    assert result["success_count"] == 1
    assert result["failure_count"] == 1
    assert result["recent_runs"][0]["status"] == "failed"
