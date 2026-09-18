"""Local desktop integration endpoints."""
import webbrowser
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/api/system", tags=["system"])


class OpenExternalRequest(BaseModel):
    url: str


ALLOWED_EXTERNAL_HOSTS = {
    "chromewebstore.google.com",
    "www.goofish.com",
}


@router.post("/open-external", response_model=dict)
async def open_external(request: OpenExternalRequest):
    """Open a small allowlisted set of external pages in the system browser."""
    parsed = urlparse(request.url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_EXTERNAL_HOSTS:
        raise HTTPException(status_code=400, detail="不允许打开该外部链接")

    if not webbrowser.open(request.url, new=2):
        raise HTTPException(status_code=503, detail="系统默认浏览器未能打开该链接")

    return {"opened": True}
