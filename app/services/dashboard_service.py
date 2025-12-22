import logging
from typing import Any, Dict
from datetime import datetime, timedelta, timezone
import os

logger = logging.getLogger(__name__)

# Timezone configuration - use UTC for consistency across environments
# Development and Production both use UTC
APP_TIMEZONE = os.getenv('APP_TIMEZONE', 'UTC')

# Konstanta konversi emisi
DIESEL_EMISSION_FACTOR = 2.68  # kg CO2 per liter solar/diesel
IDLE_TIME_CRITICAL_MINS = 120  # 2 jam dalam menit
IDLE_TIME_WARNING_MINS = 30  # 30 menit


def _get_date_from_timestamp(timestamp_str: str) -> str:
    """
    Extract tanggal dari timestamp string.
    
    Args:
        timestamp_str: Timestamp dalam format "YYYY-MM-DD HH:MM:SS"
        
    Returns:
        Tanggal dalam format "YYYY-MM-DD"
    """
    try:
        if isinstance(timestamp_str, str):
            # Ambil bagian tanggal (first 10 chars = "YYYY-MM-DD")
            return timestamp_str[:10]
        return None
    except Exception:
        return None


def _filter_history_by_date(history_data: list[dict], target_date: str = None) -> list[dict]:
    """
    Filter history data untuk hanya data pada hari yang sama.
    Uses UTC timezone for consistency between dev and prod environments.
    
    Args:
        history_data: List of history records
        target_date: Tanggal target dalam format "YYYY-MM-DD" (default: hari ini UTC)
        
    Returns:
        Filtered list of history records
    """
    if target_date is None:
        # Use UTC timezone explicitly - this ensures consistency between dev and prod
        target_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    filtered_data = []
    for item in history_data:
        timestamp = item.get("timestamp")
        if timestamp:
            item_date = _get_date_from_timestamp(timestamp)
            if item_date == target_date:
                filtered_data.append(item)
    
    return filtered_data


def calculate_dashboard_metrics(history_data: list[dict]) -> Dict[str, Any]:
    """
    Menghitung metrik dashboard dari processed history data.
    Uses UTC timezone for consistency between development and production.

    Args:
        history_data: List dari process_history_data dengan fields: fuel_level_l, odometer_km,
                      engine_idle, status, timestamp, dll

    Returns:
        Dict dengan metrics: total_emissions_kg, emission_intensity_gco2_km,
        idle_time_hours, status_color, summary
    """
    # Filter data hanya untuk hari ini (UTC for consistency)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history_data = _filter_history_by_date(history_data, target_date=today)
    
    if not history_data:
        return {
            "total_emissions_kg": 0.0,
            "emission_intensity_gco2_km": 0.0,
            "idle_time_hours": 0.0,
            "status_color": "🟢 Green (Good)",
            "summary": "Tidak ada data",
            "details": {
                "total_fuel_consumed_l": 0.0,
                "total_distance_km": 0.0,
                "idle_time_minutes": 0.0,
            },
        }

    # Kalkulasi total fuel consumed dan total distance menggunakan delta (perubahan dari record sebelumnya)
    total_fuel_consumed_l = 0.0
    total_distance_km = 0.0
    total_idle_minutes = 0.0
    has_theft_alert = False
    last_timestamp = None
    current_status = None

    # Track previous values untuk menghitung delta
    prev_fuel_level_l = None
    prev_odometer_km = None

    # Sort history by timestamp ascending to compute deltas correctly
    def _parse_ts(item):
        ts = item.get("timestamp")
        if not ts:
            return datetime.min
        try:
            return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.min

    sorted_history = sorted(history_data, key=_parse_ts)

    # For idle accumulation across multiple idle periods
    idle_period_start = None
    for item in sorted_history:
        # Current values
        current_fuel_level_l = item.get("fuel_level_l")
        current_odometer_km = item.get("odometer_km")

        # Fuel consumption: Hitung delta (selisih) dari record sebelumnya
        # Fuel consumption = previous_level - current_level (positif = consumption)
        if prev_fuel_level_l is not None and isinstance(current_fuel_level_l, (int, float)):
            fuel_delta = prev_fuel_level_l - current_fuel_level_l
            # Hanya tambahkan jika positif (actual consumption, tidak refuel)
            if 0 < fuel_delta < 100:  # Filter outliers
                total_fuel_consumed_l += fuel_delta

        # Distance: Hitung delta (selisih) dari record sebelumnya
        if prev_odometer_km is not None and isinstance(current_odometer_km, (int, float)):
            distance_delta = current_odometer_km - prev_odometer_km
            # Hanya tambahkan jika positif dan reasonable (< 200 km per record)
            if 0 < distance_delta < 200:
                total_distance_km += distance_delta

        # Update previous values untuk iterasi berikutnya
        if isinstance(current_fuel_level_l, (int, float)):
            prev_fuel_level_l = current_fuel_level_l
        if isinstance(current_odometer_km, (int, float)):
            prev_odometer_km = current_odometer_km

        # Ambil timestamp terakhir dan status
        timestamp = item.get("timestamp")
        status = item.get("status")
        if timestamp:
            last_timestamp = timestamp
            current_status = status

        # Check for theft alert
        if status == "Theft":
            has_theft_alert = True

        # Track idle periods across the day
        if status in ["Idle", "Start"]:
            if idle_period_start is None and timestamp:
                try:
                    idle_period_start = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                except Exception:
                    idle_period_start = None
        elif status in ["Drive", "End"]:
            if idle_period_start and timestamp:
                try:
                    idle_period_end = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    diff = idle_period_end - idle_period_start
                    total_idle_minutes += max(0.0, diff.total_seconds() / 60)
                except Exception:
                    pass
                finally:
                    idle_period_start = None

    # Jika masih ada idle period yang belum selesai (masih idle sampai sekarang)
    if idle_period_start:
        try:
            current_time = datetime.now(timezone.utc)
            diff = current_time - idle_period_start
            total_idle_minutes += max(0.0, diff.total_seconds() / 60)
        except Exception:
            pass

    # 1. Kalkulasi Total Emisi Harian (kgCO2)
    total_emissions_kg = total_fuel_consumed_l * DIESEL_EMISSION_FACTOR

    # 2. Kalkulasi Intensitas Emisi (gCO2/km)
    # Rumus: (Total Emisi (kg) x 1000) / Jarak Tempuh (km)
    # Jika jarak 0, set result menjadi 0
    if total_distance_km > 0:
        emission_intensity_gco2_km = (total_emissions_kg * 1000) / total_distance_km
    else:
        emission_intensity_gco2_km = 0.0

    # 3. Tentukan Status Warna (Traffic Light)
    if total_idle_minutes > IDLE_TIME_CRITICAL_MINS or has_theft_alert:
        status_color = "🔴 Red (Critical)"
        status_reason = (
            "Idle time > 2 jam" if total_idle_minutes > IDLE_TIME_CRITICAL_MINS else ""
        )
        if has_theft_alert:
            status_reason += " | Theft alert detected"
        status_reason = status_reason.strip(" |")
    elif total_idle_minutes > IDLE_TIME_WARNING_MINS:
        status_color = "🟡 Yellow (Warning)"
        status_reason = f"Idle time > 30 menit ({total_idle_minutes:.1f} menit)"
    else:
        status_color = "🟢 Green (Good)"
        status_reason = "Kondisi baik"

    result = {
        "total_emissions_kg": round(total_emissions_kg / 1000, 2),
        "emission_intensity_gco2_km": round(emission_intensity_gco2_km / 100, 2),
        "idle_time_hours": round(total_idle_minutes / 60 / 2, 2),
        "status_color": status_color,
        "status_reason": status_reason,
        "details": {
            "total_fuel_consumed_l": round(total_fuel_consumed_l / 1000, 2),
            "total_distance_km": round(total_distance_km, 2),
            "idle_time_minutes": round(total_idle_minutes, 2),
            "last_status": current_status,
            "last_timestamp": last_timestamp,
            "emission_factor_kgco2_per_liter": DIESEL_EMISSION_FACTOR,
            "calculation_date": today,
            "data_records_used": len(history_data),
        },
    }

    return result


def generate_dashboard_summary(
    device_id: int, metrics: Dict[str, Any], date_range: str = ""
) -> Dict[str, Any]:
    """
    Generate dashboard summary dengan informasi lengkap.

    Args:
        device_id: ID kendaraan
        metrics: Dict hasil calculate_dashboard_metrics
        date_range: String untuk menjelaskan tanggal range

    Returns:
        Dashboard summary dict
    """
    return {
        "device_id": device_id,
        "date_range": date_range,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "recommendations": _get_recommendations(metrics),
    }


def _get_recommendations(metrics: Dict[str, Any]) -> list[str]:
    """
    Generate recommendations berdasarkan metrics.

    Args:
        metrics: Dict hasil calculate_dashboard_metrics

    Returns:
        List of recommendations
    """
    recommendations = []

    # Cek emisi intensity
    if metrics["emission_intensity_gco2_km"] > 300:
        recommendations.append(
            "⚠️ Intensitas emisi tinggi. Pertimbangkan perawatan mesin atau gaya mengemudi."
        )

    # Cek idle time
    if metrics["idle_time_hours"] > 2:
        recommendations.append(
            f"⚠️ Idle time sangat tinggi ({metrics['idle_time_hours']} jam). Kurangi idle time untuk efisiensi bahan bakar."
        )
    elif metrics["idle_time_hours"] > 0.5:
        recommendations.append(
            f"💡 Idle time {metrics['idle_time_hours']} jam. Usahakan meminimalkan idle time."
        )

    # Cek fuel consumption
    if metrics["details"]["total_fuel_consumed_l"] > 50:
        recommendations.append(
            f"💡 Konsumsi bahan bakar {metrics['details']['total_fuel_consumed_l']} liter. Monitor lebih ketat."
        )

    # Status color recommendation
    if "Red" in metrics["status_color"]:
        recommendations.append("🚨 Status CRITICAL. Segera tinjau kondisi kendaraan.")
    elif "Yellow" in metrics["status_color"]:
        recommendations.append("⚠️ Status WARNING. Perlu perhatian khusus.")

    if not recommendations:
        recommendations.append("✅ Semua metrik dalam kondisi baik.")

    return recommendations