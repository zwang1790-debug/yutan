"""Persist a small local history of task executions for troubleshooting."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Lock

HISTORY_PATH = Path("data/task_run_history.json")
MAX_RUNS_PER_TASK = 30
_LOCK = Lock()


def _load() -> dict[str, list[dict]]:
    try:
        payload = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save(payload: dict[str, list[dict]]) -> None:
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = HISTORY_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(HISTORY_PATH)


def record_start(task_id: int, task_name: str) -> str:
    run_id = f"{task_id}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    with _LOCK:
        payload = _load()
        payload.setdefault(str(task_id), []).append({
            "run_id": run_id,
            "task_id": task_id,
            "task_name": task_name,
            "started_at": datetime.now().astimezone().isoformat(),
            "finished_at": None,
            "status": "running",
            "exit_code": None,
        })
        payload[str(task_id)] = payload[str(task_id)][-MAX_RUNS_PER_TASK:]
        _save(payload)
    return run_id


def record_finish(task_id: int, exit_code: int | None, *, manual_stop: bool = False) -> None:
    with _LOCK:
        payload = _load()
        runs = payload.get(str(task_id), [])
        current = next((item for item in reversed(runs) if item.get("status") == "running"), None)
        if current is None:
            return
        current["finished_at"] = datetime.now().astimezone().isoformat()
        current["exit_code"] = exit_code
        current["status"] = "stopped" if manual_stop else ("success" if exit_code == 0 else "failed")
        _save(payload)


def get_task_history(task_id: int) -> dict:
    with _LOCK:
        runs = list(_load().get(str(task_id), []))
    finished = [item for item in runs if item.get("status") != "running"]
    return {
        "task_id": task_id,
        "total_runs": len(finished),
        "success_count": sum(item.get("status") == "success" for item in finished),
        "failure_count": sum(item.get("status") == "failed" for item in finished),
        "stopped_count": sum(item.get("status") == "stopped" for item in finished),
        "running": any(item.get("status") == "running" for item in runs),
        "recent_runs": list(reversed(runs[-10:])),
    }


def get_all_task_history(task_ids: list[int]) -> dict[int, dict]:
    return {task_id: get_task_history(task_id) for task_id in task_ids}
