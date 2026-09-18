"""Build a support bundle without exporting credentials or login state."""
from __future__ import annotations

import json
import os
import platform
import re
import sys
import zipfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Iterable

from src.services.log_diagnosis_service import diagnose_log
from src.utils import resolve_task_log_path


_SECRET_KEY = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|auth(?:orization)?|cookie|session|secret|password|token)"
)
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|authorization|cookie|session|secret|password|token)\s*[:=]\s*([^\s,;]+)"
)
_BEARER = re.compile(r"(?i)\bBearer\s+[^\s]+")
_COOKIE_HEADER = re.compile(r"(?i)(Cookie\s*:\s*)([^\r\n]+)")
_MAX_LOG_BYTES = 40_000


def sanitize_text(value: str) -> str:
    """Mask common credential formats while preserving useful error context."""
    text = _BEARER.sub("Bearer [REDACTED]", str(value or ""))
    text = _COOKIE_HEADER.sub(r"\1[REDACTED]", text)
    return _SECRET_ASSIGNMENT.sub(r"\1=[REDACTED]", text)


def sanitize_mapping(value):
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _SECRET_KEY.search(str(key)) else sanitize_mapping(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize_mapping(item) for item in value]
    if isinstance(value, str):
        return sanitize_text(value)
    return value


def _read_tail(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - _MAX_LOG_BYTES))
            return sanitize_text(handle.read().decode("utf-8", errors="replace"))
    except OSError as exc:
        return f"[无法读取日志: {sanitize_text(str(exc))}]"


def _task_summary(task) -> dict:
    return {
        "id": task.id,
        "task_name": sanitize_text(task.task_name),
        "keyword": sanitize_text(task.keyword),
        "decision_mode": task.decision_mode,
        "enabled": task.enabled,
        "is_running": task.is_running,
        "max_pages": task.max_pages,
        "personal_only": task.personal_only,
        "analyze_images": task.analyze_images,
        "min_price": task.min_price,
        "max_price": task.max_price,
        "cron_configured": bool(task.cron),
        "prompt_files": [task.ai_prompt_base_file, task.ai_prompt_criteria_file],
    }


def build_diagnostic_bundle(tasks: Iterable) -> bytes:
    """Return a ZIP containing only sanitized, support-relevant diagnostics."""
    task_list = list(tasks)
    logs = {}
    for task in task_list:
        if task.id is None:
            continue
        path = Path(resolve_task_log_path(task.id, task.task_name))
        if path.exists():
            logs[f"task-{task.id}.log"] = _read_tail(path)

    diagnosis_text = "\n\n".join(logs.values())
    manifest = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
        "note": "本诊断包已排除 API Key、Cookie、Token、Authorization、密码和闲鱼登录态。",
        "task_count": len(task_list),
        "log_count": len(logs),
    }
    safe_diagnostics = {
        "status": diagnose_log(diagnosis_text) if diagnosis_text else diagnose_log(""),
        "environment": {
            "env_file_exists": Path(".env").exists(),
            "login_state_exists": Path("xianyu_state.json").exists(),
            "browser_runtime_exists": Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ".playwright-browsers")).exists(),
            "data_directory_exists": Path("data").exists(),
            "logs_directory_exists": Path("logs").exists(),
        },
    }

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        archive.writestr("diagnostics.json", json.dumps(sanitize_mapping(safe_diagnostics), ensure_ascii=False, indent=2))
        archive.writestr("tasks.json", json.dumps([_task_summary(task) for task in task_list], ensure_ascii=False, indent=2))
        for name, content in logs.items():
            archive.writestr(f"logs/{name}", content)
        archive.writestr(
            "README.txt",
            "这是脱敏诊断包，不包含 API Key、Cookie 或闲鱼登录态。\n"
            "可将整个 ZIP 提交给售后或开发人员分析。\n",
        )
    return buffer.getvalue()
