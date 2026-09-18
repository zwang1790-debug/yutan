"""任务启动前的本地环境预检。"""

import os
from pathlib import Path

from src.config import STATE_FILE
from src.infrastructure.config.settings import AISettings, scraper_settings
from src.rotation import load_state_files
from src.services.account_strategy_service import normalize_account_strategy


def _check(key: str, label: str, passed: bool, detail: str, fix: str = "") -> dict:
    return {"key": key, "label": label, "status": "pass" if passed else "error", "passed": passed, "detail": detail, "fix": fix}


def build_task_preflight(task) -> dict:
    checks: list[dict] = []
    decision_mode = getattr(task, "decision_mode", "ai") or "ai"
    strategy = normalize_account_strategy(getattr(task, "account_strategy", None), getattr(task, "account_state_file", None))

    if decision_mode == "ai":
        ai_ready = AISettings().is_configured() and bool(os.getenv("OPENAI_API_KEY", "").strip())
        checks.append(_check("ai", "AI 配置", ai_ready, "AI 地址、模型和密钥已配置" if ai_ready else "AI 配置不完整", "前往设置 > AI，保存配置并测试连接。" if not ai_ready else ""))
        criteria_file = str(getattr(task, "ai_prompt_criteria_file", "") or "").strip()
        criteria_ready = bool(criteria_file) and Path(criteria_file).is_file()
        checks.append(_check("criteria", "AI 分析标准", criteria_ready, "任务分析标准文件已找到" if criteria_ready else "任务缺少有效的 AI 分析标准文件", "编辑任务并重新生成 AI 分析标准。" if not criteria_ready else ""))

    if strategy == "fixed":
        account_path = str(getattr(task, "account_state_file", "") or "").strip()
        account_ready = bool(account_path) and Path(account_path).is_file()
        checks.append(_check("account", "固定闲鱼账号", account_ready, "任务绑定的登录态文件已找到" if account_ready else "任务绑定的登录态文件不存在", "前往账号管理重新导入登录态，或改用自动账号模式。" if not account_ready else ""))
    else:
        root_ready = Path(scraper_settings.state_file or STATE_FILE).is_file()
        account_files = load_state_files(os.getenv("ACCOUNT_STATE_DIR", "state"))
        account_ready = root_ready or bool(account_files)
        checks.append(_check("account", "闲鱼登录态", account_ready, "已找到可用的闲鱼登录态" if account_ready else "未找到闲鱼登录态文件", "前往账号管理导入登录态后再启动任务。" if not account_ready else ""))

    browser_path = Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", ".playwright-browsers"))
    browser_ready = browser_path.exists()
    checks.append(_check("browser", "浏览器运行时", browser_ready, "Playwright 浏览器已就绪" if browser_ready else "未找到 Playwright 浏览器运行时", "请重新安装 Windows 版本，或运行浏览器依赖安装脚本。" if not browser_ready else ""))
    blocking = [check for check in checks if not check["passed"]]
    return {"task_id": getattr(task, "id", None), "task_name": getattr(task, "task_name", ""), "ready": not blocking, "checks": checks, "blocking_count": len(blocking), "summary": "启动条件检查通过" if not blocking else f"发现 {len(blocking)} 项启动前问题"}
