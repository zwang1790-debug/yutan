"""
结果文件管理路由
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from enum import Enum

from pydantic import BaseModel
from urllib.parse import quote

from src.services.price_history_service import build_price_history_insights
from src.services.result_export_service import build_results_csv
from src.services.result_file_service import (
    enrich_records_with_price_insight,
    validate_result_filename,
)
from src.services.result_storage_service import (
    build_result_ndjson,
    delete_result_file_records,
    list_result_filenames,
    load_all_result_records,
    load_result_blacklist_keywords,
    load_visible_result_item_ids,
    query_result_records,
    result_file_exists,
    result_item_exists,
    save_result_blacklist_keywords,
    update_item_status,
)
from src.services.profit_estimate_service import calculate_profit, save_profit_estimate
from src.services.inventory_service import save_inventory_record
from src.services.opportunity_score_service import sort_records_by_opportunity
from src.services.business_summary_service import load_result_business_summary


router = APIRouter(prefix="/api/results", tags=["results"])

DEFAULT_EXPORT_FILENAME = "export.csv"


def _build_download_headers(export_name: str) -> dict[str, str]:
    ascii_name = export_name.encode("ascii", "ignore").decode("ascii")
    if ascii_name != export_name or not ascii_name:
        ascii_name = DEFAULT_EXPORT_FILENAME
    encoded_name = quote(export_name, safe="")
    return {
        "Content-Disposition": (
            f'attachment; filename="{ascii_name}"; '
            f"filename*=UTF-8''{encoded_name}"
        )
    }


@router.get("/files")
async def get_result_files():
    """获取所有结果文件列表"""
    return {"files": await list_result_filenames()}


@router.get("/files/{filename:path}")
async def download_result_file(filename: str):
    """下载指定的结果文件"""
    if ".." in filename or filename.startswith("/"):
        return {"error": "非法的文件路径"}
    if not filename.endswith(".jsonl") or not await result_file_exists(filename):
        return {"error": "文件不存在"}
    return Response(
        content=await build_result_ndjson(filename),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete("/files/{filename:path}")
async def delete_result_file(filename: str):
    """删除指定的结果文件"""
    if ".." in filename or filename.startswith("/"):
        raise HTTPException(status_code=400, detail="非法的文件路径")
    if not filename.endswith(".jsonl"):
        raise HTTPException(status_code=400, detail="只能删除 .jsonl 文件")
    deleted_rows = await delete_result_file_records(filename)
    if deleted_rows <= 0:
        raise HTTPException(status_code=404, detail="文件不存在")
    return {"message": f"文件 {filename} 已成功删除"}


@router.get("/{filename}")
async def get_result_file_content(
    filename: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    recommended_only: bool = Query(False),  # 兼容旧参数，等价于 ai_recommended_only
    ai_recommended_only: bool = Query(False),
    keyword_recommended_only: bool = Query(False),
    include_hidden: bool = Query(False),
    sort_by: str = Query("crawl_time"),
    sort_order: str = Query("desc"),
):
    """读取指定的 .jsonl 文件内容，支持分页、筛选和排序"""
    if ai_recommended_only and keyword_recommended_only:
        raise HTTPException(status_code=400, detail="AI推荐筛选与关键词推荐筛选不能同时开启。")

    if recommended_only and not ai_recommended_only and not keyword_recommended_only:
        ai_recommended_only = True

    try:
        validate_result_filename(filename)
        if sort_by == "opportunity_score":
            all_items = await load_all_result_records(
                filename,
                ai_recommended_only=ai_recommended_only,
                keyword_recommended_only=keyword_recommended_only,
                sort_by="crawl_time",
                sort_order="desc",
                include_hidden=include_hidden,
            )
            enriched = sort_records_by_opportunity(
                enrich_records_with_price_insight(all_items, filename), sort_order
            )
            total_items = len(enriched)
            offset = (page - 1) * limit
            paginated_results = enriched[offset : offset + limit]
        else:
            total_items, items = await query_result_records(
                filename,
                ai_recommended_only=ai_recommended_only,
                keyword_recommended_only=keyword_recommended_only,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                limit=limit,
                include_hidden=include_hidden,
            )
            paginated_results = enrich_records_with_price_insight(items, filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取结果文件时出错: {exc}")
    if total_items <= 0 and not await result_file_exists(filename):
        raise HTTPException(status_code=404, detail="结果文件未找到")
    return {
        "total_items": total_items,
        "page": page,
        "limit": limit,
        "items": paginated_results
    }


@router.get("/{filename}/insights")
async def get_result_file_insights(filename: str):
    try:
        validate_result_filename(filename)
        keyword = filename.replace("_full_data.jsonl", "")
        visible_item_ids = load_visible_result_item_ids(filename)
        insights = build_price_history_insights(keyword, visible_item_ids=visible_item_ids)
        insights["business_summary"] = await load_result_business_summary(
            filename, visible_item_ids
        )
        return insights
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/{filename}/export")
async def export_result_file_content(
    filename: str,
    recommended_only: bool = Query(False),
    ai_recommended_only: bool = Query(False),
    keyword_recommended_only: bool = Query(False),
    include_hidden: bool = Query(False),
    sort_by: str = Query("crawl_time"),
    sort_order: str = Query("desc"),
):
    if ai_recommended_only and keyword_recommended_only:
        raise HTTPException(status_code=400, detail="AI推荐筛选与关键词推荐筛选不能同时开启。")
    if recommended_only and not ai_recommended_only and not keyword_recommended_only:
        ai_recommended_only = True

    try:
        validate_result_filename(filename)
        results = await load_all_result_records(
            filename,
            ai_recommended_only=ai_recommended_only,
            keyword_recommended_only=keyword_recommended_only,
            sort_by=sort_by,
            sort_order=sort_order,
            include_hidden=include_hidden,
        )
        enriched_results = enrich_records_with_price_insight(results, filename)
        if sort_by == "opportunity_score":
            enriched_results = sort_records_by_opportunity(enriched_results, sort_order)
        csv_text = build_results_csv(enriched_results)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"导出结果文件时出错: {exc}")
    if not results and not await result_file_exists(filename):
        raise HTTPException(status_code=404, detail="结果文件未找到")

    export_name = filename.replace(".jsonl", ".csv")
    headers = _build_download_headers(export_name)
    return Response(content=csv_text, media_type="text/csv; charset=utf-8", headers=headers)


class ItemStatus(str, Enum):
    ACTIVE = "active"
    HIDDEN = "hidden"
    EXPIRED = "expired"


class UpdateStatusRequest(BaseModel):
    status: ItemStatus


class BlacklistRulesRequest(BaseModel):
    keywords: list[str]


class ProfitEstimateRequest(BaseModel):
    purchase_price: float
    resale_price: float
    platform_fee: float = 0
    shipping_cost: float = 0
    other_cost: float = 0


class InventoryRecordRequest(BaseModel):
    status: str
    actual_purchase_price: float | None = None
    actual_sale_price: float | None = None
    actual_platform_fee: float | None = None
    actual_shipping_cost: float | None = None
    actual_other_cost: float | None = None
    notes: str | None = None


@router.patch("/{filename}/items/{item_id}/status")
async def patch_item_status(filename: str, item_id: str, body: UpdateStatusRequest):
    """更新指定商品的状态（active/hidden/expired）"""
    try:
        validate_result_filename(filename)
        updated = await update_item_status(filename, item_id, body.status.value)
        if not updated:
            raise HTTPException(status_code=404, detail="商品未找到")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "状态已更新", "status": body.status.value}


@router.put("/{filename}/items/{item_id}/profit-estimate")
async def put_profit_estimate(
    filename: str, item_id: str, body: ProfitEstimateRequest
):
    try:
        validate_result_filename(filename)
        if not await result_item_exists(filename, item_id):
            raise HTTPException(status_code=404, detail="商品未找到，无法保存利润估算。")
        estimate = save_profit_estimate(filename, item_id, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "利润估算已保存", "estimate": calculate_profit(estimate)}


@router.put("/{filename}/items/{item_id}/inventory")
async def put_inventory_record(
    filename: str, item_id: str, body: InventoryRecordRequest
):
    try:
        validate_result_filename(filename)
        if not await result_item_exists(filename, item_id):
            raise HTTPException(status_code=404, detail="商品未找到，无法保存经营台账。")
        record = save_inventory_record(
            filename,
            item_id,
            body.model_dump(exclude_unset=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "经营台账已保存", "record": record}


@router.get("/{filename}/blacklist-rules")
async def get_result_blacklist_rules(filename: str):
    try:
        validate_result_filename(filename)
        keywords = await load_result_blacklist_keywords(filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"keywords": keywords}


@router.put("/{filename}/blacklist-rules")
async def put_result_blacklist_rules(filename: str, body: BlacklistRulesRequest):
    try:
        validate_result_filename(filename)
        keywords = await save_result_blacklist_keywords(filename, body.keywords)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"message": "黑名单规则已更新", "keywords": keywords}
