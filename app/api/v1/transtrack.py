from typing import Any
from fastapi import APIRouter, Query
from app.services.transtrack_service import (
    get_devices,
    get_history,
    simplify_devices,
    process_history_data,
)

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


@router.get("/devices-summary")
async def devices_summary(
    lang: str = Query("en", description="Language, e.g. 'en'"),
    user_api_hash: str = Query(..., description="user_api_hash token from login")
) -> list[dict]:
    """Return simplified list of devices (id and name only) from Transtrack API.

    Query params:
    - lang: language code (default 'en')
    - user_api_hash: token obtained from login

    Returns:
    - List of devices with only {id, name} fields
    """
    full_devices = await get_devices(lang=lang, user_api_hash=user_api_hash)
    return simplify_devices(full_devices)


@router.get("/history")
async def history(
    lang: str = Query("en", description="Language, e.g. 'en'"),
    user_api_hash: str = Query(..., description="user_api_hash token from login"),
    device_id: int = Query(..., description="Device ID from devices list"),
    snap_to_road: bool = Query(False, description="Snap route to road (smoothing)"),
    from_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    from_time: str | None = Query(None, description="Start time (HH:MM:SS)"),
    to_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    to_time: str | None = Query(None, description="End time (HH:MM:SS)"),
) -> Any:
    """Return history perjalanan kendaraan from Transtrack API.

    Query params:
    - lang: language code (default 'en')
    - user_api_hash: token obtained from login
    - device_id: id kendaraan
    - snap_to_road: boolean flag to smooth route
    - from_date/from_time, to_date/to_time: date/time range
    """
    return await get_history(
        lang=lang,
        user_api_hash=user_api_hash,
        device_id=device_id,
        from_date=from_date,
        from_time=from_time,
        to_date=to_date,
        to_time=to_time,
        snap_to_road=snap_to_road,
    )


@router.get("/processed-history")
async def processed_history(
    lang: str = Query("en", description="Language, e.g. 'en'"),
    user_api_hash: str = Query(..., description="user_api_hash token from login"),
    device_id: int = Query(..., description="Device ID from devices list"),
    snap_to_road: bool = Query(False, description="Snap route to road (smoothing)"),
    from_date: str | None = Query(None, description="Start date (YYYY-MM-DD)"),
    from_time: str | None = Query(None, description="Start time (HH:MM:SS)"),
    to_date: str | None = Query(None, description="End date (YYYY-MM-DD)"),
    to_time: str | None = Query(None, description="End time (HH:MM:SS)"),
) -> list[dict]:
    """Return processed history dengan 17 field yang diakumulasikan dari sensor data.

    Mengekstrak: timestamp, device_id, latitude, longitude, speed, ignition, motion,
    odometer_km, engine_hours, fuel_level_l, rpm, battery_voltage, sat, hdop, pdop, valid, status.

    Query params sama dengan /history

    Returns:
    - List of processed items dengan field: timestamp, device_id, lat, lng, speed, ignition,
      motion, odometer_km, engine_hours, fuel_level_l, rpm, battery_voltage, sat, hdop, pdop,
      valid, status
    """
    full_history = await get_history(
        lang=lang,
        user_api_hash=user_api_hash,
        device_id=device_id,
        from_date=from_date,
        from_time=from_time,
        to_date=to_date,
        to_time=to_time,
        snap_to_road=snap_to_road,
    )
    return process_history_data(full_history)