"""API Key authentication for VeriCoach backend."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from backend.config import BackendSettings, get_backend_settings

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(
    api_key: str | None = Security(API_KEY_HEADER),
    settings: BackendSettings = Depends(get_backend_settings),
) -> str | None:
    """Validate X-API-Key header against configured authorized keys."""
    if not settings.require_api_key:
        return api_key or "anonymous-dev"

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required X-API-Key header",
        )

    if api_key not in settings.api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid X-API-Key provided",
        )

    return api_key
