"""
结果导出服务
"""
import csv
from io import StringIO


EXPORT_HEADERS = [
    "任务名称",
    "搜索关键字",
    "商品ID",
    "商品标题",
    "当前售价",
    "发布时间",
    "卖家昵称",
    "AI是否推荐",
    "分析来源",
    "原因",
    "价格观察次数",
    "价格最低值",
    "价格最高值",
    "市场均价",
    "市场P25",
    "市场P50",
    "市场P75",
    "有效估值样本",
    "原始市场样本",
    "排除样本",
    "性价比分数",
    "性价比标签",
    "机会分",
    "机会标签",
    "建议最高收货价",
    "建议挂售价",
    "定价状态",
    "保守变现价",
    "建议快速出货价",
    "定价最高收货价",
    "预计利润",
    "预计毛利率",
    "风险说明",
    "商品链接",
]


def build_results_csv(records: list[dict]) -> str:
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_HEADERS)
    writer.writeheader()

    for record in records:
        item = record.get("商品信息", {}) or {}
        seller = record.get("卖家信息", {}) or {}
        ai_analysis = record.get("ai_analysis", {}) or {}
        price_insight = record.get("price_insight", {}) or {}
        opportunity = record.get("opportunity_assessment", {}) or {}
        pricing = record.get("pricing_assessment", {}) or {}
        writer.writerow(
            {
                "任务名称": record.get("任务名称", ""),
                "搜索关键字": record.get("搜索关键字", ""),
                "商品ID": item.get("商品ID", ""),
                "商品标题": item.get("商品标题", ""),
                "当前售价": item.get("当前售价", ""),
                "发布时间": item.get("发布时间", ""),
                "卖家昵称": seller.get("卖家昵称") or item.get("卖家昵称", ""),
                "AI是否推荐": "是" if ai_analysis.get("is_recommended") else "否",
                "分析来源": ai_analysis.get("analysis_source", ""),
                "原因": ai_analysis.get("reason", ""),
                "价格观察次数": price_insight.get("observation_count", ""),
                "价格最低值": price_insight.get("min_price", ""),
                "价格最高值": price_insight.get("max_price", ""),
                "市场均价": price_insight.get("market_avg_price", ""),
                "市场P25": price_insight.get("market_p25_price", ""),
                "市场P50": price_insight.get("market_p50_price", ""),
                "市场P75": price_insight.get("market_p75_price", ""),
                "有效估值样本": price_insight.get("market_sample_count", ""),
                "原始市场样本": price_insight.get("market_raw_sample_count", ""),
                "排除样本": price_insight.get("market_excluded_sample_count", ""),
                "性价比分数": ai_analysis.get("value_score", price_insight.get("deal_score", "")),
                "性价比标签": ai_analysis.get("value_summary", price_insight.get("deal_label", "")),
                "机会分": opportunity.get("score", ""),
                "机会标签": opportunity.get("label", ""),
                "建议最高收货价": pricing.get("recommended_max_purchase_price") if pricing.get("recommended_max_purchase_price") is not None else opportunity.get("recommended_max_purchase_price", ""),
                "建议挂售价": pricing.get("suggested_listing_price") if pricing.get("suggested_listing_price") is not None else opportunity.get("suggested_listing_price", ""),
                "定价状态": pricing.get("label", ""),
                "保守变现价": pricing.get("conservative_resale_price", ""),
                "建议快速出货价": pricing.get("quick_sale_price", ""),
                "定价最高收货价": pricing.get("recommended_max_purchase_price", ""),
                "预计利润": pricing.get("expected_profit") if pricing.get("expected_profit") is not None else opportunity.get("expected_profit", ""),
                "预计毛利率": pricing.get("expected_margin") if pricing.get("expected_margin") is not None else opportunity.get("expected_margin", ""),
                "风险说明": "；".join(opportunity.get("risk_notes", []) or []),
                "商品链接": item.get("商品链接", ""),
            }
        )

    return buffer.getvalue()
