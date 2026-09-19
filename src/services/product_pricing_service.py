"""Product subscription catalog used by the in-app commercial plan page.

This is intentionally a catalog, not an entitlement checker. Payment and
device-license enforcement can consume the same plan ids when those modules
are introduced.
"""
from __future__ import annotations

from typing import Any


def _text(zh: str, en: str) -> dict[str, str]:
    return {"zh": zh, "en": en}


def _feature(zh: str, en: str) -> dict[str, str]:
    return _text(zh, en)


def _plan(
    *,
    plan_id: str,
    kind: str,
    name_zh: str,
    name_en: str,
    description_zh: str,
    description_en: str,
    price: float,
    billing_period: str,
    availability: str,
    badge_zh: str,
    badge_en: str,
    features: list[dict[str, str]],
    note_zh: str,
    note_en: str,
    recommended: bool = False,
) -> dict[str, Any]:
    return {
        "id": plan_id,
        "kind": kind,
        "name": _text(name_zh, name_en),
        "description": _text(description_zh, description_en),
        "price": price,
        "currency": "CNY",
        "billing_period": billing_period,
        "availability": availability,
        "badge": _text(badge_zh, badge_en),
        "features": features,
        "note": _text(note_zh, note_en),
        "recommended": recommended,
    }


def get_product_pricing() -> dict[str, Any]:
    """Return the single source of truth for the current commercial offer."""
    return {
        "product_name": _text("鱼探 Radar", "YuTan Radar"),
        "positioning": _text(
            "闲鱼行情与捡漏决策助手",
            "Goofish market intelligence and sourcing assistant",
        ),
        "pricing_version": "2026-09",
        "last_reviewed": "2026-09-09",
        "commercial_stage": "manual_delivery",
        "plans": [
            _plan(
                plan_id="trial_7d",
                kind="software",
                name_zh="7 天体验",
                name_en="7-day trial",
                description_zh="先跑通一个品类，再决定是否长期使用。",
                description_en="Validate one category before committing long term.",
                price=9.9,
                billing_period="7_days",
                availability="available",
                badge_zh="低门槛",
                badge_en="Low-risk start",
                features=[
                    _feature("核心监控、结果查看与价格参考", "Core monitoring, results, and price references"),
                    _feature("用户自备 AI API Key，费用透明", "Bring your own AI API key with transparent usage cost"),
                    _feature("到期后不自动续费", "No automatic renewal after the trial"),
                ],
                note_zh="购买年卡时可抵扣 9.9 元，人工确认订单后处理。",
                note_en="The CNY 9.90 trial fee can be credited toward an annual plan after manual order confirmation.",
            ),
            _plan(
                plan_id="personal_launch",
                kind="software",
                name_zh="个人版·首发",
                name_en="Personal · launch",
                description_zh="给第一批高频卖家准备的限量入门价。",
                description_en="A limited launch price for the first wave of active sellers.",
                price=149,
                billing_period="annual",
                availability="available",
                badge_zh="首发限量",
                badge_en="Limited launch",
                features=[
                    _feature("监控任务、结果、日志与通知能力", "Monitoring tasks, results, logs, and notifications"),
                    _feature("市场价格区间、历史位置与机会判断", "Market bands, historical position, and opportunity signals"),
                    _feature("12 个月版本更新与基础排障", "12 months of updates and basic troubleshooting"),
                    _feature("单台 Windows 设备使用", "Use on one Windows device"),
                    _feature("AI API 费用由用户自理", "AI API usage is paid by the user"),
                ],
                note_zh="前 200 位或首发期结束，以先到者为准；与个人常规版权益一致。",
                note_en="Available to the first 200 customers or during the launch period, whichever comes first; same core rights as Personal.",
            ),
            _plan(
                plan_id="personal_annual",
                kind="software",
                name_zh="个人版·常规",
                name_en="Personal · standard",
                description_zh="个人卖家的长期主力方案。",
                description_en="The long-term default plan for individual sellers.",
                price=199,
                billing_period="annual",
                availability="available",
                badge_zh="长期主推",
                badge_en="Best default",
                recommended=True,
                features=[
                    _feature("监控任务、结果、日志与通知能力", "Monitoring tasks, results, logs, and notifications"),
                    _feature("市场价格区间、历史位置与机会判断", "Market bands, historical position, and opportunity signals"),
                    _feature("12 个月版本更新与基础排障", "12 months of updates and basic troubleshooting"),
                    _feature("单台 Windows 设备使用", "Use on one Windows device"),
                    _feature("AI API 费用由用户自理", "AI API usage is paid by the user"),
                ],
                note_zh="个人卖家默认推荐；不包含远程安装和代运营服务。",
                note_en="Recommended for individual sellers; remote setup and managed operations are separate services.",
            ),
            _plan(
                plan_id="personal_monthly",
                kind="software",
                name_zh="个人版·月卡",
                name_en="Personal · monthly",
                description_zh="适合短期测试和暂时观望的卖家。",
                description_en="For short-term testing and sellers who are still evaluating the workflow.",
                price=29,
                billing_period="monthly",
                availability="available",
                badge_zh="短期试用",
                badge_en="Short-term",
                features=[
                    _feature("个人版核心监控、结果与价格参考", "Personal monitoring, results, and price references"),
                    _feature("用户自备 AI API Key，费用透明", "Bring your own AI API key with transparent usage cost"),
                    _feature("按月续费，到期不自动续费", "Monthly term with no automatic renewal"),
                    _feature("单台 Windows 设备使用", "Use on one Windows device"),
                ],
                note_zh="月卡适合短期验证；长期使用建议选择 199 元年卡。",
                note_en="Best for short-term validation; the CNY 199 annual plan is better for ongoing use.",
            ),
            _plan(
                plan_id="professional_annual",
                kind="software",
                name_zh="专业版·升级",
                name_en="Professional · upgrade",
                description_zh="面向高频倒货卖家的后续升级档。",
                description_en="A future upgrade tier for high-frequency resellers.",
                price=299,
                billing_period="annual",
                availability="coming_soon",
                badge_zh="后续开放",
                badge_en="Coming next",
                features=[
                    _feature("更高任务规模与更多品类模板", "Higher task capacity and more category templates"),
                    _feature("优先更新与经营复盘能力", "Priority updates and operating review tools"),
                    _feature("适合高客单、高频率的专业卖家", "For professional sellers with higher ticket volume"),
                    _feature("具体额度以授权模块上线公告为准", "Exact limits will be announced with entitlement support"),
                ],
                note_zh="授权与额度限制尚未上线，当前不要按专业版收款。",
                note_en="Entitlements and usage limits are not live yet; do not sell this tier until the license module ships.",
            ),
            _plan(
                plan_id="remote_setup",
                kind="service",
                name_zh="远程部署服务",
                name_en="Remote setup",
                description_zh="一次性协助安装、配置与首次环境诊断。",
                description_en="One-time help with installation, configuration, and first diagnostics.",
                price=69,
                billing_period="one_time",
                availability="available",
                badge_zh="可选服务",
                badge_en="Optional service",
                features=[
                    _feature("安装 Windows 版本并确认能启动", "Install the Windows build and verify startup"),
                    _feature("协助配置 AI、登录态与一个监控任务", "Configure AI, login state, and one monitoring task"),
                    _feature("不包含持续代运营或无限次调参", "Does not include managed operations or unlimited tuning"),
                ],
                note_zh="可选的一次性服务，适合希望有人协助完成首次配置的用户。",
                note_en="An optional one-time service for users who want help completing their first setup.",
            ),
        ],
        "policies": {
            "api_cost": _text(
                "大模型 API、代理和第三方通知渠道费用由用户自行承担。",
                "LLM API, proxy, and third-party notification costs are paid by the user.",
            ),
            "license": _text(
                "当前交付口径按 1 台 Windows 设备；换机和特殊授权由人工处理。",
                "Current delivery is scoped to one Windows device; device changes and exceptions are handled manually.",
            ),
            "updates": _text(
                "年卡包含购买后 12 个月版本更新；续费价格按届时公告。",
                "Annual plans include updates for 12 months after purchase; renewal pricing follows the then-current notice.",
            ),
            "support": _text(
                "基础售后解决安装、配置和明显故障，不承诺代运营、自动成交或收益。",
                "Basic support covers installation, configuration, and clear faults; it does not promise managed operations, automated sales, or profit.",
            ),
            "delivery": _text(
                "购买后由客服人工确认订单并发送安装包、配置说明和授权码。",
                "After purchase, support confirms the order and sends the installer, setup notes, and license code.",
            ),
        },
        "sales_guardrails": [
            _text("对外主打“行情与决策辅助”，不要承诺稳定捡漏或保证盈利。", "Position it as market intelligence and decision support, never as guaranteed deals or profit."),
            _text("首发个人版与常规个人版权益保持一致，用优惠换取首批案例和反馈。", "Keep launch and standard Personal rights aligned; use the discount to earn early cases and feedback."),
            _text("专业版在授权模块上线前只做价格锚点，不作为当前可售档位。", "Use Professional as a price anchor until entitlement support is live; do not sell it yet."),
        ],
    }
