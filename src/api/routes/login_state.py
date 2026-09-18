"""
登录状态管理路由
"""
import os
import json
import aiofiles
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/login-state", tags=["login-state"])
STATE_FILE = Path("xianyu_state.json")


class LoginStateUpdate(BaseModel):
    """登录状态更新模型"""
    content: str


@router.post("", response_model=dict)
async def update_login_state(
    data: LoginStateUpdate,
):
    """接收前端发送的登录状态JSON字符串，并保存到 xianyu_state.json"""
    state_file = STATE_FILE

    try:
        # 验证是否是有效的JSON
        json.loads(data.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="提供的内容不是有效的JSON格式。")

    try:
        async with aiofiles.open(state_file, 'w', encoding='utf-8') as f:
            await f.write(data.content)
        return {"message": f"登录状态文件 '{state_file}' 已成功更新。"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"写入登录状态文件时出错: {e}")


@router.delete("", response_model=dict)
async def delete_login_state():
    """删除 xianyu_state.json 文件"""
    state_file = STATE_FILE

    if os.path.exists(state_file):
        try:
            os.remove(state_file)
            return {"message": "登录状态文件已成功删除。"}
        except OSError as e:
            raise HTTPException(status_code=500, detail=f"删除登录状态文件时出错: {e}")

    return {"message": "登录状态文件不存在，无需删除。"}


@router.get("/status", response_model=dict)
async def get_login_state_status():
    """检查登录态文件是否存在、可解析且最近有更新。"""
    if not STATE_FILE.exists():
        return {
            "exists": False,
            "valid_json": False,
            "path": str(STATE_FILE),
            "updated_at": None,
            "message": "未找到登录态文件，请登录闲鱼后导入。",
        }

    try:
        content = STATE_FILE.read_text(encoding="utf-8")
        parsed = json.loads(content)
        valid_json = isinstance(parsed, (dict, list))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        valid_json = False

    updated_at = None
    try:
        updated_at = STATE_FILE.stat().st_mtime
    except OSError:
        pass

    return {
        "exists": True,
        "valid_json": valid_json,
        "path": str(STATE_FILE),
        "updated_at": updated_at,
        "message": "登录态文件有效" if valid_json else "登录态文件存在，但 JSON 无法解析，请重新导入。",
    }
