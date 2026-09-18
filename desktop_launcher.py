"""
桌面启动入口
使用 PyInstaller 打包后作为单一可执行文件的入口，自动启动 FastAPI 服务并打开浏览器。
"""
import os
import sys
import time
import webbrowser
import asyncio
from pathlib import Path

import uvicorn

# For onedir builds, writable data and bundled browsers live beside the EXE.
# In source mode, keep the project directory as the working root.
BASE_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent
)


def _prepare_environment() -> None:
    """确保工作目录和模块路径正确"""
    os.chdir(BASE_DIR)
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))
    bundled_browsers = BASE_DIR / ".playwright-browsers"
    if bundled_browsers.exists():
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(bundled_browsers))


def run_app() -> None:
    """启动 FastAPI 应用并自动打开浏览器"""
    _prepare_environment()

    from src.app import app
    from src.infrastructure.config.settings import settings

    # 先尝试打开浏览器，稍等服务起来
    url = f"http://127.0.0.1:{settings.server_port}"
    webbrowser.open(url)
    time.sleep(0.5)

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=settings.server_port,
        log_level="info",
        reload=False,
    )


def run_worker() -> None:
    """Run the crawler worker when a frozen build starts a child process."""
    _prepare_environment()
    from spider_v2 import main as spider_main

    asyncio.run(spider_main())


if __name__ == "__main__":
    if "--worker" in sys.argv:
        # Remove the launcher-only flag before spider_v2 parses its arguments.
        sys.argv.remove("--worker")
        run_worker()
    else:
        run_app()
