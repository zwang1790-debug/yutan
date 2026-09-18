from types import SimpleNamespace

from src.services import task_preflight_service


def _task(**overrides):
    values = {
        "id": 1,
        "task_name": "测试任务",
        "decision_mode": "ai",
        "account_strategy": "auto",
        "account_state_file": None,
        "ai_prompt_criteria_file": "prompts/missing.txt",
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_ai_task_blocks_when_ai_or_criteria_is_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(task_preflight_service, "AISettings", lambda: SimpleNamespace(is_configured=lambda: False))
    monkeypatch.setattr(task_preflight_service, "scraper_settings", SimpleNamespace(state_file=str(tmp_path / "state.json")))
    monkeypatch.setattr(task_preflight_service, "load_state_files", lambda _path: [])
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(tmp_path / "browsers"))

    result = task_preflight_service.build_task_preflight(_task())

    assert result["ready"] is False
    assert {check["key"] for check in result["checks"] if not check["passed"]} == {"ai", "criteria", "account", "browser"}


def test_keyword_task_does_not_require_ai(monkeypatch, tmp_path):
    state_file = tmp_path / "state.json"
    state_file.write_text("{}", encoding="utf-8")
    browser_path = tmp_path / "browsers"
    browser_path.mkdir()
    monkeypatch.setattr(task_preflight_service, "scraper_settings", SimpleNamespace(state_file=str(state_file)))
    monkeypatch.setattr(task_preflight_service, "load_state_files", lambda _path: [])
    monkeypatch.setenv("PLAYWRIGHT_BROWSERS_PATH", str(browser_path))

    result = task_preflight_service.build_task_preflight(_task(decision_mode="keyword"))

    assert result["ready"] is True
    assert {check["key"] for check in result["checks"]} == {"account", "browser"}
