import httpx
import logging
from typing import Any, Dict
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

TRANSTRACK_DEVICES_URL = "https://telematics.transtrack.id/api/get_devices"


async def get_devices(lang: str, user_api_hash: str) -> Dict[str, Any]:
    """
    Fetch daftar device dari Transtrack API.

    Args:
        lang: bahasa, contohnya 'en'
        user_api_hash: token autentikasi yang diterima saat login

    Returns:
        Parsed JSON response dari Transtrack

    Raises:
        HTTPException jika request gagal
    """
    params = {
        "lang": lang,
        "user_api_hash": user_api_hash
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(TRANSTRACK_DEVICES_URL, params=params)

            try:
                data = resp.json()
            except ValueError:
                logger.error("Invalid JSON response from Transtrack get_devices")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Invalid response from Transtrack API"
                )

            if resp.status_code == 200:
                return data
            else:
                # If API returns error payload, forward its message if available
                msg = data.get("message") if isinstance(data, dict) else None
                detail = msg or f"Transtrack API returned status {resp.status_code}"
                logger.warning(f"get_devices failed: {resp.status_code} - {detail}")
                raise HTTPException(
                    status_code=resp.status_code if resp.status_code >= 400 else status.HTTP_400_BAD_REQUEST,
                    detail=detail
                )

    except httpx.RequestError as exc:
        logger.error(f"Request error calling Transtrack get_devices: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot reach Transtrack API"
        )
