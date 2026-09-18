import json
import zipfile
from io import BytesIO
from pathlib import Path

from src.services import diagnostic_export_service as service


class _Task:
    id = 7
    task_name = "测试任务"
    keyword = "显卡 token=should-not-leak"
    decision_mode = "ai"
    enabled = True
    is_running = False
    max_pages = 2
    personal_only = True
    analyze_images = True
    min_price = "100"
    max_price = "200"
    cron = "*/15 * * * *"
    ai_prompt_base_file = "prompts/base_prompt.txt"
    ai_prompt_criteria_file = "prompts/test.txt"


def test_sanitize_text_masks_credentials():
    value = "Authorization: Bearer abc cookie=xyz OPENAI_API_KEY=secret"
    result = service.sanitize_text(value)
    assert "abc" not in result
    assert "xyz" not in result
    assert "secret" not in result
    assert "[REDACTED]" in result


def test_build_diagnostic_bundle_contains_only_safe_files(tmp_path, monkeypatch):
    log = tmp_path / "task.log"
    log.write_text("OPENAI_API_KEY=secret\n正常日志\ncookie=abc", encoding="utf-8")
    monkeypatch.setattr(service, "resolve_task_log_path", lambda *_args: str(log))
    monkeypatch.setattr(Path, "exists", lambda self: self == log or self.name in {"data", "logs"})

    content = service.build_diagnostic_bundle([_Task()])
    with zipfile.ZipFile(BytesIO(content)) as archive:
        names = set(archive.namelist())
        assert "xianyu_state.json" not in names
        assert "tasks.json" in names
        task_payload = json.loads(archive.read("tasks.json"))
        assert "account_state_file" not in task_payload[0]
        log_payload = archive.read("logs/task-7.log").decode("utf-8")
        assert "secret" not in log_payload
        assert "abc" not in log_payload
