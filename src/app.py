"""
新架构的主应用入口
整合所有路由和服务
"""
from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.api.routes import (
    dashboard,
    tasks,
    logs,
    settings,
    prompts,
    results,
    login_state,
    websocket,
    accounts,
    backup,
    auth,
    license,
    system,
)
from src.api.dependencies import (
    set_process_service,
    set_scheduler_service,
    set_task_generation_service,
)
from src.services.task_service import TaskService
from src.services.process_service import ProcessService
from src.services.scheduler_service import SchedulerService
from src.services.task_log_cleanup_service import cleanup_task_logs
from src.services.task_generation_service import TaskGenerationService
from src.services.task_run_history_service import record_finish, record_start
from src.services.release_info_service import VERSION as APP_VERSION
from src.infrastructure.persistence.sqlite_bootstrap import bootstrap_sqlite_storage
from src.infrastructure.persistence.sqlite_connection import sqlite_connection
from src.infrastructure.persistence.sqlite_task_repository import SqliteTaskRepository
from src.infrastructure.config.settings import settings as app_settings
from src.services.web_auth_service import SESSION_COOKIE_NAME, get_session_username
from src.services.license_service import get_license_status


# 全局服务实例
process_service = ProcessService()
scheduler_service = SchedulerService(process_service)
task_generation_service = TaskGenerationService()


async def _sync_task_runtime_status(task_id: int, is_running: bool) -> None:
    task_service = TaskService(SqliteTaskRepository())
    task = await task_service.get_task(task_id)
    if not task or task.is_running == is_running:
        return
    await task_service.update_task_status(task_id, is_running)
    if is_running:
        record_start(task_id, task.task_name)
    else:
        record_finish(
            task_id,
            process_service.last_exit_codes.get(task_id),
            manual_stop=task_id in process_service.manual_stop_ids,
        )
        process_service.manual_stop_ids.discard(task_id)
    await websocket.broadcast_message(
        "task_status_changed",
        {"id": task_id, "is_running": is_running},
    )


process_service.set_lifecycle_hooks(
    on_started=lambda task_id: _sync_task_runtime_status(task_id, True),
    on_stopped=lambda task_id: _sync_task_runtime_status(task_id, False),
)

# 设置全局 ProcessService 实例供依赖注入使用
set_process_service(process_service)
set_scheduler_service(scheduler_service)
set_task_generation_service(task_generation_service)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("正在启动应用...")
    bootstrap_sqlite_storage()
    cleanup_task_logs(keep_days=app_settings.task_log_retention_days)

    # 重置所有任务状态为停止
    task_repo = SqliteTaskRepository()
    task_service = TaskService(task_repo)
    tasks_list = await task_service.get_all_tasks()

    for task in tasks_list:
        if task.is_running:
            await task_service.update_task_status(task.id, False)
        # Child processes are owned by this application process. After a restart,
        # any persisted "running" entry is therefore an interrupted prior run.
        record_finish(task.id, None)

    # Do not schedule or execute customer work after trial/license expiry.
    if get_license_status().entitled:
        await scheduler_service.reload_jobs(tasks_list)
        scheduler_service.start()
    else:
        print("授权未生效，已跳过定时任务启动")

    print("应用启动完成")
    process_service.start_license_monitor()

    yield

    # 关闭时
    print("正在关闭应用...")
    await process_service.stop_license_monitor()
    scheduler_service.stop()
    await process_service.stop_all()
    print("应用已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="鱼探 Radar",
    description="闲鱼机会监测与智能分析",
    version=APP_VERSION,
    lifespan=lifespan
)


class WebAuthMiddleware(BaseHTTPMiddleware):
    """Protect every API request while leaving the SPA shell and login public."""

    async def dispatch(self, request, call_next):
        path = request.url.path
        if path.startswith("/api/"):
            username = get_session_username(request.cookies.get(SESSION_COOKIE_NAME))
            if not username:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "登录已失效，请重新登录"},
                )
            if not (path.startswith("/api/license/") or path in {"/api/settings/pricing", "/api/settings/diagnostics", "/api/backup/download", "/api/backup/download/full", "/api/backup/diagnostic"}):
                entitlement = get_license_status()
                if not entitlement.entitled:
                    return JSONResponse(
                        status_code=402,
                        content={"detail": entitlement.message, "code": entitlement.code},
                    )
        return await call_next(request)


app.add_middleware(WebAuthMiddleware)

# 注册路由
app.include_router(auth.router)
app.include_router(tasks.router)
app.include_router(dashboard.router)
app.include_router(logs.router)
app.include_router(settings.router)
app.include_router(prompts.router)
app.include_router(results.router)
app.include_router(login_state.router)
app.include_router(websocket.router)
app.include_router(accounts.router)
app.include_router(backup.router)
app.include_router(license.router)
app.include_router(system.router)

# 挂载静态文件
# 旧的静态文件目录（用于截图等）
app.mount("/static", StaticFiles(directory="static"), name="static")

# 挂载 Vue 3 前端构建产物
# 注意：需要在所有 API 路由之后挂载，以避免覆盖 API 路由
if os.path.exists("dist"):
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")


@app.get("/health/live")
async def liveness_check():
    """Process liveness probe. It intentionally avoids external dependencies."""
    return {"status": "healthy"}


@app.get("/health/ready")
async def readiness_check():
    """Readiness probe for local and container deployments."""
    checks = {}
    try:
        with sqlite_connection() as conn:
            conn.execute("SELECT 1").fetchone()
        checks["database"] = True
    except Exception:
        checks["database"] = False

    required_directories = ("data", "state", "logs", "images", "jsonl", "price_history")
    checks["storage"] = all(
        Path(directory).exists() and os.access(directory, os.W_OK)
        for directory in required_directories
    )
    checks["scheduler"] = bool(getattr(scheduler_service.scheduler, "running", False))
    ready = all(checks.values())
    payload = {"status": "ready" if ready else "not_ready", "checks": checks}
    return JSONResponse(status_code=200 if ready else 503, content=payload)


@app.get("/health")
async def health_check():
    """Backward-compatible readiness endpoint."""
    return await readiness_check()


@app.get("/favicon.svg")
async def favicon_svg():
    """Serve the branded browser icon from the built frontend."""
    return FileResponse("dist/favicon.svg")


@app.get("/favicon.ico")
async def favicon_ico():
    """Serve the Windows/browser-compatible icon when available."""
    return FileResponse("dist/app-icon.ico")


# 主页路由 - 服务 Vue 3 SPA
from fastapi import Request
from fastapi.responses import FileResponse
from fastapi.responses import JSONResponse

@app.get("/")
async def read_root(request: Request):
    """提供 Vue 3 SPA 的主页面"""
    if os.path.exists("dist/index.html"):
        return FileResponse("dist/index.html")
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "前端构建产物不存在，请先运行 cd web-ui && npm run build"}
        )


# Catch-all 路由 - 处理所有前端路由（必须放在最后）
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """
    Catch-all 路由，将所有非 API 请求重定向到 index.html
    这样可以支持 Vue Router 的 HTML5 History 模式
    """
    # 如果请求的是静态资源（如 favicon.ico），返回 404
    if full_path.endswith(('.ico', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.css', '.js', '.json')):
        return JSONResponse(status_code=404, content={"error": "资源未找到"})

    # 其他所有路径都返回 index.html，让前端路由处理
    if os.path.exists("dist/index.html"):
        return FileResponse("dist/index.html")
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "前端构建产物不存在，请先运行 cd web-ui && npm run build"}
        )


if __name__ == "__main__":
    import uvicorn
    from src.infrastructure.config.settings import settings

    print(f"启动新架构应用，端口: {app_settings.server_port}")
    uvicorn.run(app, host="0.0.0.0", port=app_settings.server_port)
