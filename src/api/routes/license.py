from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.services.license_service import LicenseError, activate_license, get_license_status
from src.api.dependencies import get_scheduler_service, get_task_service
from src.services.scheduler_service import SchedulerService
from src.services.task_service import TaskService

router = APIRouter(prefix="/api/license", tags=["license"])


class ActivateLicenseRequest(BaseModel):
    code: str = Field(min_length=10, max_length=4096)


@router.get("/status")
async def license_status():
    return get_license_status().to_dict()


@router.post("/activate")
async def license_activate(
    payload: ActivateLicenseRequest,
    task_service: TaskService = Depends(get_task_service),
    scheduler_service: SchedulerService = Depends(get_scheduler_service),
):
    try:
        status = activate_license(payload.code)
        await scheduler_service.reload_jobs(await task_service.get_all_tasks())
        scheduler_service.start()
        return status.to_dict()
    except LicenseError as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": str(exc)}) from exc
