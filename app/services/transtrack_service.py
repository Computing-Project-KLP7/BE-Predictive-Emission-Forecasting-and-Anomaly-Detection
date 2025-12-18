import httpx
import logging
from typing import Any, Dict
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

TRANSTRACK_DEVICES_URL = "https://telematics.transtrack.id/api/get_devices"
TRANSTRACK_HISTORY_URL = "https://telematics.transtrack.id/api/get_history"


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


async def get_history(
    lang: str,
    user_api_hash: str,
    device_id: int,
    from_date: str | None = None,
    from_time: str | None = None,
    to_date: str | None = None,
    to_time: str | None = None,
    snap_to_road: bool | None = None,
) -> Dict[str, Any]:
    """
    Fetch history perjalanan kendaraan dari Transtrack API.

    Args:
        lang: bahasa (e.g. 'en')
        user_api_hash: token autentikasi
        device_id: ID kendaraan
        from_date/to_date: tanggal dalam format yang diharapkan API (mis. '2023-01-01')
        from_time/to_time: waktu dalam format yang diharapkan API (mis. '00:00:00')
        snap_to_road: optional smoothing flag

    Returns:
        Parsed JSON response dari Transtrack

    Raises:
        HTTPException jika request gagal
    """
    params: dict = {
        "lang": lang,
        "user_api_hash": user_api_hash,
        "device_id": device_id,
    }

    # Hanya tambahkan param jika tidak None
    if from_date:
        params["from_date"] = from_date
    if from_time:
        params["from_time"] = from_time
    if to_date:
        params["to_date"] = to_date
    if to_time:
        params["to_time"] = to_time
    if snap_to_road is not None:
        # API mungkin mengharapkan 1/0
        params["snap_to_road"] = 1 if snap_to_road else 0

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.get(TRANSTRACK_HISTORY_URL, params=params)

            try:
                data = resp.json()
            except ValueError:
                logger.error("Invalid JSON response from Transtrack get_history")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Invalid response from Transtrack API"
                )

            if resp.status_code == 200:
                return data
            else:
                msg = data.get("message") if isinstance(data, dict) else None
                detail = msg or f"Transtrack API returned status {resp.status_code}"
                logger.warning(f"get_history failed: {resp.status_code} - {detail}")
                raise HTTPException(
                    status_code=resp.status_code if resp.status_code >= 400 else status.HTTP_400_BAD_REQUEST,
                    detail=detail
                )

    except httpx.RequestError as exc:
        logger.error(f"Request error calling Transtrack get_history: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot reach Transtrack API"
        )
