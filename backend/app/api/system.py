"""System status endpoints for the operator UI sidebar."""

from __future__ import annotations

from typing import Any

import httpx
from fastapi import APIRouter
from pydantic import BaseModel

from app.config import get_settings

router = APIRouter(
    prefix="/system",
    tags=["system"],
)


class ComponentStatus(BaseModel):
    name: str
    status: str
    detail: str | None = None


class SystemStatusResponse(BaseModel):
    environment: str
    backend: ComponentStatus
    mcp: ComponentStatus
    crm: ComponentStatus
    billing: ComponentStatus


async def _probe(
    url: str,
    *,
    timeout: float = 1.5,
) -> tuple[str, str | None]:
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(url)

        if response.status_code < 500:
            return "ok", f"HTTP {response.status_code}"

        return "degraded", f"HTTP {response.status_code}"
    except Exception as exc:  # noqa: BLE001
        return "down", str(exc)


@router.get(
    "/status",
    response_model=SystemStatusResponse,
)
async def get_system_status() -> SystemStatusResponse:
    settings = get_settings()

    mcp_status, mcp_detail = await _probe(
        settings.mcp_server_url.replace("/mcp", "/health")
        if settings.mcp_server_url.endswith("/mcp")
        else f"{settings.mcp_server_url}/health"
    )

    # MCP may not expose /health; fall back to base reachability.
    if mcp_status == "down":
        mcp_base = settings.mcp_server_url.rstrip("/")
        if mcp_base.endswith("/mcp"):
            mcp_base = mcp_base[: -len("/mcp")]
        mcp_status, mcp_detail = await _probe(mcp_base or "http://127.0.0.1:8200")

    crm_status, crm_detail = await _probe(
        f"{settings.crm_base_url.rstrip('/')}/health"
    )
    billing_status, billing_detail = await _probe(
        f"{settings.billing_base_url.rstrip('/')}/health"
    )

    return SystemStatusResponse(
        environment=settings.environment,
        backend=ComponentStatus(
            name="backend",
            status="ok",
            detail=settings.app_name,
        ),
        mcp=ComponentStatus(
            name="mcp",
            status=mcp_status,
            detail=mcp_detail,
        ),
        crm=ComponentStatus(
            name="crm",
            status=crm_status,
            detail=crm_detail,
        ),
        billing=ComponentStatus(
            name="billing",
            status=billing_status,
            detail=billing_detail,
        ),
    )


@router.get("/info")
async def get_system_info() -> dict[str, Any]:
    settings = get_settings()

    return {
        "app_name": settings.app_name,
        "environment": settings.environment,
        "adk_model": settings.adk_model,
        "otel_enabled": settings.otel_enabled,
        "auth_configured": bool(settings.google_oauth_client_id),
    }
