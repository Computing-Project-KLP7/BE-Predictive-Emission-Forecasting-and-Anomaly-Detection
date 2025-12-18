from typing import Any
from fastapi import APIRouter, Query
from app.services.transtrack_service import get_devices

router = APIRouter()


@router.get("/devices")
async def devices(
    lang: str = Query("en", description="Language, e.g. 'en'"),
    user_api_hash: str = Query(..., description="user_api_hash token from login")
) -> Any:
    """Return list of devices from Transtrack API.

    Query params:
    - lang: language code (default 'en')
    - user_api_hash: token obtained from login
    """
    return await get_devices(lang=lang, user_api_hash=user_api_hash)