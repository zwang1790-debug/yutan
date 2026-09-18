"""本地数据备份与恢复路由。"""
from __future__ import annotations

import io
import json
import os
import shutil
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.api.dependencies import get_process_service, get_scheduler_service, get_task_service
from src.infrastructure.config.settings import reload_settings
from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.services.process_service import ProcessService
from src.services.scheduler_service import SchedulerService
from src.services.task_service import TaskService
from src.services.diagnostic_export_service import build_diagnostic_bundle


router = APIRouter(prefix="/api/backup", tags=["backup"])
BACKUP_ROOT = Path(".")
SAFE_BACKUP_DIRS = ("data", "jsonl", "price_history", "prompts", "images")
SAFE_BACKUP_FILES = ("config.json",)
FULL_BACKUP_DIRS = SAFE_BACKUP_DIRS + ("state", "logs")
FULL_BACKUP_FILES = SAFE_BACKUP_FILES + (".env", "xianyu_state.json")
BACKUP_INFO_NAME = "BACKUP_INFO.json"
LEGACY_BACKUP_INFO_NAME = "BACKUP_INFO.txt"
MAX_BACKUP_FILES = 50_000
MAX_BACKUP_BYTES = 256 * 1024 * 1024


def _safe_member(name: str, allowed_roots: tuple[str, ...]) -> bool:
    path = Path(name)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and path.parts
        and path.parts[0] in set(allowed_roots)
    )


def _add_path(archive: zipfile.ZipFile, path: Path) -> None:
    if not path.exists():
        return
    if path.is_file():
        archive.write(
            path,
            arcname=path.resolve().relative_to(BACKUP_ROOT.resolve()).as_posix(),
        )
        return
    for child in path.rglob("*"):
        if child.is_file():
            archive.write(
                child,
                arcname=child.resolve().relative_to(BACKUP_ROOT.resolve()).as_posix(),
            )


def _build_backup_bytes(*, include_sensitive: bool = False) -> bytes:
    directories = FULL_BACKUP_DIRS if include_sensitive else SAFE_BACKUP_DIRS
    files = FULL_BACKUP_FILES if include_sensitive else SAFE_BACKUP_FILES
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path_name in files + directories:
            _add_path(archive, BACKUP_ROOT / path_name)
        archive.writestr(
            BACKUP_INFO_NAME,
            json.dumps(
                {
                    "format_version": 1,
                    "backup_type": "full" if include_sensitive else "safe",
                    "created_at": datetime.now().astimezone().isoformat(),
                    "contains_sensitive_data": include_sensitive,
                },
                ensure_ascii=False,
                indent=2,
            ),
        )
    return buffer.getvalue()


def _archive_metadata(archive: zipfile.ZipFile) -> dict:
    if BACKUP_INFO_NAME not in archive.namelist():
        # Backward-compatible handling for existing local full backups.
        return {"backup_type": "full", "format_version": 0}
    try:
        metadata = json.loads(archive.read(BACKUP_INFO_NAME).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError) as exc:
        raise ValueError("备份元数据无效。") from exc
    if not isinstance(metadata, dict) or metadata.get("backup_type") not in {"safe", "full"}:
        raise ValueError("备份类型无效。")
    return metadata


def _validate_archive(archive: zipfile.ZipFile) -> tuple[list[str], dict]:
    metadata = _archive_metadata(archive)
    allowed = (
        FULL_BACKUP_FILES + FULL_BACKUP_DIRS
        if metadata["backup_type"] == "full"
        else SAFE_BACKUP_FILES + SAFE_BACKUP_DIRS
    )
    members = [name for name in archive.namelist() if name and not name.endswith("/")]
    restore_members = [
        name
        for name in members
        if name not in {BACKUP_INFO_NAME, LEGACY_BACKUP_INFO_NAME}
    ]
    if not restore_members or len(restore_members) > MAX_BACKUP_FILES:
        raise ValueError("备份文件数量不合法。")
    if any(not _safe_member(member, allowed) for member in restore_members):
        raise ValueError("备份文件包含不允许恢复的路径。")
    if sum(info.file_size for info in archive.infolist()) > MAX_BACKUP_BYTES:
        raise ValueError("备份文件解压后过大。")
    bad_member = archive.testzip()
    if bad_member:
        raise ValueError(f"备份文件损坏：{bad_member}")
    return restore_members, metadata


def _restore_members(archive: zipfile.ZipFile, members: list[str]) -> None:
    for member in members:
        target = BACKUP_ROOT / member
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".restore-tmp")
        try:
            with archive.open(member) as source, temporary.open("wb") as destination:
                shutil.copyfileobj(source, destination)
            os.replace(temporary, target)
        finally:
            if temporary.exists():
                temporary.unlink(missing_ok=True)


@router.get("/status")
async def get_backup_status():
    sizes = {}
    for name in FULL_BACKUP_FILES + FULL_BACKUP_DIRS:
        path = BACKUP_ROOT / name
        if path.is_file():
            sizes[name] = path.stat().st_size
        elif path.is_dir():
            sizes[name] = sum(item.stat().st_size for item in path.rglob("*") if item.is_file())
    safe_total = sum(sizes.get(name, 0) for name in SAFE_BACKUP_FILES + SAFE_BACKUP_DIRS)
    return {
        "items": sizes,
        "total_bytes": safe_total,
        "full_backup_bytes": sum(sizes.values()),
        "safe_backup_excludes": [".env", "xianyu_state.json", "state", "logs"],
    }


@router.get("/download")
async def download_backup():
    """Download a share-safe backup that excludes secrets and login state."""
    content = _build_backup_bytes(include_sensitive=False)
    filename = f"YuTanRadar-safe-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/download/full")
async def download_full_backup():
    """Download a migration backup. This contains credentials and login state."""
    content = _build_backup_bytes(include_sensitive=True)
    filename = f"YuTanRadar-full-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/diagnostic")
async def download_diagnostic_bundle(
    task_service: TaskService = Depends(get_task_service),
):
    """Download a support bundle with credentials and login state removed."""
    tasks = await task_service.get_all_tasks()
    content = build_diagnostic_bundle(tasks)
    filename = f"YuTanRadar-diagnostic-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/restore")
async def restore_backup(
    request: Request,
    process_service: ProcessService = Depends(get_process_service),
    task_service: TaskService = Depends(get_task_service),
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
):
    if any(process and process.returncode is None for process in process_service.processes.values()):
        raise HTTPException(status_code=409, detail="请先停止所有监控任务，再恢复备份。")

    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="备份文件为空。")
    if len(content) > MAX_BACKUP_BYTES:
        raise HTTPException(status_code=413, detail="备份文件过大。")

    try:
        archive = zipfile.ZipFile(io.BytesIO(content))
        members, metadata = _validate_archive(archive)
    except (zipfile.BadZipFile, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"备份文件无效：{exc}") from exc

    safety_backup = _build_backup_bytes(include_sensitive=True)
    safety_path = Path(tempfile.gettempdir()) / f"YuTanRadar-before-restore-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    safety_path.write_bytes(safety_backup)

    try:
        _restore_members(archive, members)
    except OSError as exc:
        try:
            with zipfile.ZipFile(io.BytesIO(safety_backup)) as safety_archive:
                safety_members, _ = _validate_archive(safety_archive)
                _restore_members(safety_archive, safety_members)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail=f"恢复备份失败，已尝试回滚；恢复前备份保存在：{safety_path}；原因：{exc}") from exc

    reload_settings()
    bootstrap_sqlite_storage()
    await scheduler_service.reload_jobs(await task_service.get_all_tasks())

    return {
        "message": "备份恢复成功；已重新加载任务与配置，建议重启应用以应用端口等启动参数。",
        "safety_backup": str(safety_path),
        "backup_type": metadata["backup_type"],
        "restart_recommended": True,
    }
