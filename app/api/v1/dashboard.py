from typing import Any
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from app.services.transtrack_service import get_history, process_history_data
from app.services.dashboard_service import calculate_dashboard_metrics, generate_dashboard_summary

router = APIRouter()


@router.get("/metrics")
async def dashboard_metrics(
    lang: str = Query("en", description="Language, e.g. 'en'"),
    user_api_hash: str = Query(..., description="user_api_hash token from login"),
    device_id: int = Query(..., description="Device ID from devices list"),
    snap_to_road: bool = Query(False, description="Snap route to road (smoothing)"),
) -> dict[str, Any]:
    """
    Dashboard metrics endpoint untuk menampilkan real-time metrics:
    1. Total Emisi Harian (kgCO2): Total Liter BBM x 2.68
    2. Intensitas Emisi (gCO2/km): (Total Emisi (kg) x 1000) / Jarak Tempuh (km)
    3. Idle Time: Dihitung dari waktu idle terakhir hingga sekarang
    4. Status Warna (Traffic Light):
       - 🔴 Red (Critical): Idle Time > 2 jam OR Theft alert
       - 🟡 Yellow (Warning): Idle Time > 30 menit tapi < 2 jam
       - 🟢 Green (Good): Sisanya

    Query params:
    - lang: language code (default 'en')
    - user_api_hash: token obtained from login (required)
    - device_id: id kendaraan (required)
    - snap_to_road: boolean flag to smooth route (optional)

    Returns:
    - Dashboard metrics dengan emissions, intensity, idle time, status, dan recommendations
    """
    # Get current date (UTC for consistency between dev and prod)
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    start_time = "00:00:00"
    end_time = now.strftime("%H:%M:%S")

    # Fetch history data dari transtrack untuk hari ini
    full_history = await get_history(
        lang=lang,
        user_api_hash=user_api_hash,
        device_id=device_id,
        from_date=today,
        from_time=start_time,
        to_date=today,
        to_time=end_time,
        snap_to_road=snap_to_road,
    )

    # Process history untuk dapatkan fields yang diperlukan
    history_data = process_history_data(full_history)

    # Calculate metrics
    metrics = calculate_dashboard_metrics(history_data)

    # Generate summary dengan recommendations
    date_range = f"Today ({today}) up to {end_time}"
    summary = generate_dashboard_summary(device_id, metrics, date_range)
    return summary
