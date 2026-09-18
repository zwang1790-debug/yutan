"""将任务日志中的常见错误转换为用户可理解的诊断结果。"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class DiagnosisRule:
    category: str
    title: str
    severity: str
    patterns: tuple[str, ...]
    advice: str


RULES = (
    DiagnosisRule("login", "闲鱼登录态或风控异常", "high", ("登录", "cookie", "cookies", "未登录", "403", "401", "风控", "验证码"), "重新导入闲鱼登录态，确认账号能正常打开闲鱼网页，并适当降低任务频率。"),
    DiagnosisRule("network", "闲鱼网络或页面访问异常", "high", ("timeout", "timed out", "连接", "network", "net::", "dns", "代理"), "检查网络和代理设置；先用浏览器打开闲鱼，再降低并发或重试。"),
    DiagnosisRule("ai", "AI 接口或分析异常", "high", ("openai", "ai分析", "AI分析", "api key", "apikey", "rate limit", "模型", "json解析", "JSON解析"), "检查 AI 地址、模型和密钥，并在设置页测试连接；必要时关闭结构化输出兼容选项。"),
    DiagnosisRule("parse", "商品数据解析异常", "medium", ("解析失败", "parse", "字段缺失", "商品列表为空", "未找到商品"), "检查闲鱼页面是否变化，先用小页数任务验证；如果持续出现，保留日志用于版本修复。"),
    DiagnosisRule("storage", "本地文件或权限异常", "high", ("permission", "权限", "no such file", "找不到文件", "sqlite", "database", "写入失败"), "确认安装目录和数据目录可写，避免把程序放在受限目录；必要时运行备份后重新安装。"),
)


def diagnose_log(content: str) -> dict:
    text = content or ""
    matches = []
    lowered = text.lower()
    for rule in RULES:
        hit = next((pattern for pattern in rule.patterns if pattern.lower() in lowered), None)
        if hit:
            matches.append({"category": rule.category, "title": rule.title, "severity": rule.severity, "matched": hit, "advice": rule.advice})

    if not matches:
        if re.search(r"(失败|error|exception|traceback)", text, re.IGNORECASE):
            return {"status": "unknown", "title": "发现未分类错误", "summary": "日志包含错误信息，但暂时无法准确归类。", "advice": "请导出诊断包或提交最近日志，便于进一步分析。", "matches": []}
        return {"status": "ok", "title": "暂未发现明显错误", "summary": "最近日志没有匹配到常见失败模式。", "advice": "如果没有抓到商品，请检查任务筛选条件、登录态和闲鱼页面访问情况。", "matches": []}

    primary = matches[0]
    return {"status": "error", "title": primary["title"], "summary": f"最近日志命中 {len(matches)} 类异常，主要问题：{primary['title']}。", "advice": primary["advice"], "matches": matches}
