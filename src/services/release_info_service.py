"""Product release metadata shown in the local support page."""
from __future__ import annotations

PRODUCT_NAME = "鱼探 Radar"
VERSION = "2.1.2"
RELEASE_DATE = "2026-09-19"


def get_release_info() -> dict:
    return {
        "product_name": PRODUCT_NAME,
        "version": VERSION,
        "release_date": RELEASE_DATE,
        "build_type": "Windows 本地版",
        "support_items": [
            "任务启动前环境预检与一键修复",
            "闲鱼登录态、AI 配置和浏览器运行时诊断",
            "任务运行历史、成功/失败统计",
            "脱敏诊断包导出",
            "本地备份与恢复",
        ],
        "release_notes": [
            "升级 Windows 商业版构建版本至 2.1.2。",
            "统一购买、设备授权和本地数据保护流程。",
            "新增任务运行历史，记录最近 30 次执行结果。",
            "新增任务成功、失败、手动停止统计。",
            "新增脱敏诊断包，便于售后排查且不包含 API Key、Cookie 和登录态。",
            "完善任务启动前检查和日志自动诊断。",
        ],
        "support_steps": [
            "先在系统状态页运行一键诊断。",
            "确认闲鱼网页可以正常打开且登录态有效。",
            "查看任务日志并点击“诊断最近日志”。",
            "仍无法解决时，导出脱敏诊断包提交售后。",
        ],
    }
