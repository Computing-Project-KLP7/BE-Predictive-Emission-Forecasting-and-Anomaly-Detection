import httpx
import logging
import re
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


def simplify_devices(devices_response: Dict[str, Any]) -> list[dict]:
    """
    Ekstrak field-field penting dari response devices.

    Args:
        devices_response: Full response dari get_devices

    Returns:
        List of dicts dengan field: id, name, online, time, speed, total_distance,
        lat, lng, altitude, plate_number (dari device_data), driver_name (dari driver_data)
    """
    simplified = []

    # devices_response adalah list of groups dengan struktur:
    # [{"id": 0, "title": "...", "items": [...]}, ...]
    if isinstance(devices_response, list):
        for group in devices_response:
            items = group.get("items", [])
            for item in items:
                device_dict = {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "online": item.get("online"),
                    "time": item.get("time"),
                    "speed": item.get("speed"),
                    "total_distance": item.get("total_distance"),
                    "lat": item.get("lat"),
                    "lng": item.get("lng"),
                    "altitude": item.get("altitude"),
                }

                # Extract nested fields
                device_data = item.get("device_data", {})
                if isinstance(device_data, dict):
                    device_dict["plate_number"] = device_data.get("plate_number")

                driver_data = item.get("driver_data", {})
                if isinstance(driver_data, dict):
                    device_dict["driver_name"] = driver_data.get("name")

                simplified.append(device_dict)

    return simplified


# Status mapping untuk history
STATUS_MAP = {
    1: "Drive",
    2: "Idle",
    3: "Start",
    4: "End",
    5: "Ack"
}


# ===== SENSOR DATA PROCESSING FUNCTIONS =====

def parse_other_string(other_str: str) -> Dict[str, Any]:
    """
    Mem-parsing string sensor 'other' menggunakan regular expression.
    Format: <key>value<key2>value2<...

    Args:
        other_str: String sensor data

    Returns:
        Dictionary dengan key-value pairs, boolean untuk ignition/motion, float untuk values lain
    """
    if not other_str:
        return {}

    # Regex pattern untuk menemukan <tag>nilai<tag_berikutnya
    pattern = re.compile(r'<(\w+)>([^<]*)<')
    matches = pattern.findall(other_str)

    data = {}
    for key, value in matches:
        key_lower = key.lower()
        if key_lower in ['ignition', 'motion']:
            # Konversi tag boolean
            data[key] = value.lower() == 'true'
        else:
            try:
                # Coba konversi nilai sensor ke float/angka
                data[key] = float(value)
            except ValueError:
                data[key] = value

    return data


def process_history_data(history_response: Dict[str, Any]) -> list[dict]:
    """
    Memproses history data dari API untuk mengekstrak 16 kolom yang diminta
    dengan parsing sensor 'other', faktor skala, dan transformasi nilai.

    Args:
        history_response: Response dari get_history API

    Returns:
        List of dicts dengan 16 field: timestamp, device_id, latitude, longitude,
        speed, ignition, motion, odometer_km, engine_hours, fuel_level_l, rpm,
        battery_voltage, sat, hdop, pdop, valid, status
    """
    rows = []

    # Iterasi data items dari history response
    items = history_response.get("items", []) if isinstance(history_response, dict) else []

    for group in items:
        # Jika group adalah dict dengan struktur {status, items: [...]}
        group_items = group.get("items", []) if isinstance(group, dict) else []

        for item in group_items:
            # ===== BASE JSON FIELDS (Direct Access) =====
            timestamp = item.get("time")
            device_id = item.get("device_id")
            latitude = item.get("lat")
            longitude = item.get("lng")
            speed = item.get("speed")  # speed_kmh

            # ===== PARSE SENSOR DATA ('other' string) =====
            other_data = parse_other_string(item.get("other", ""))

            # --- IMPLEMENTASI IO TAG & SKALA ---

            # 1. Odometer: io87 / 1000 (Fallback to io24)
            raw_odometer = other_data.get("io87") or other_data.get("io24")
            odometer_km = (
                raw_odometer / 1000
                if isinstance(raw_odometer, (int, float))
                else None
            )

            # 2. Fuel Level: io85 / 10 (Fallback to io115)
            raw_fuel_level = other_data.get("io85") or other_data.get("io115")
            fuel_level_l = (
                raw_fuel_level / 10 if isinstance(raw_fuel_level, (int, float)) else None
            )

            # 3. RPM: io84
            rpm = other_data.get("io84")

            # --- EKSTRAKSI FIELD LAIN DARI 'other' ---
            ignition = other_data.get("ignition")
            motion = other_data.get("motion")
            engine_hours = other_data.get("enginehours")
            battery_voltage = other_data.get("power")
            sat = other_data.get("sat")
            hdop = other_data.get("hdop")
            pdop = other_data.get("pdop")

            # --- FIELD KHUSUS (Valid) ---
            # 'valid' diinfer: True jika jumlah satelit lebih dari 3
            valid = True if isinstance(sat, (int, float)) and sat > 3 else False

            # --- STATUS (dari group) ---
            status_code = group.get("status") if isinstance(group, dict) else None
            status_str = STATUS_MAP.get(status_code, None)

            # 4. Kumpulkan Data (16 Kolom yang Diminta)
            rows.append({
                "timestamp": timestamp,
                "device_id": device_id,
                "latitude": latitude,
                "longitude": longitude,
                "speed": speed,
                "ignition": ignition,
                "motion": motion,
                "odometer_km": odometer_km,
                "engine_hours": engine_hours,
                "fuel_level_l": fuel_level_l,
                "rpm": rpm,
                "battery_voltage": battery_voltage,
                "sat": sat,
                "hdop": hdop,
                "pdop": pdop,
                "valid": valid,
                "status": status_str,
            })

    return rows

