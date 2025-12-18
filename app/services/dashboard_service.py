import logging
from typing import Any, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Konstanta konversi emisi
DIESEL_EMISSION_FACTOR = 2.68  # kg CO2 per liter solar/diesel
IDLE_TIME_CRITICAL_MINS = 120  # 2 jam dalam menit
IDLE_TIME_WARNING_MINS = 30  # 30 menit


def calculate_dashboard_metrics(history_data: list[dict]) -> Dict[str, Any]:
    """
    Menghitung metrik dashboard dari processed history data.

    Args:
        history_data: List dari process_history_data dengan fields: fuel_level_l, odometer_km,
                      engine_idle, status, dll

    Returns:
        Dict dengan metrics: total_emissions_kg, emission_intensity_gco2_km,
        idle_time_hours, status_color, summary
    """
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

    # Kalkulasi total fuel consumed dan total distance
    total_fuel_consumed_l = 0.0
    total_distance_km = 0.0
    current_idle_time_mins = 0.0
    has_theft_alert = False
    last_timestamp = None
    current_status = None
    
    # Untuk tracking idle period: dari kapan idle dimulai sampai kapan berakhir
    idle_start_time = None
    idle_end_time = None
    is_currently_idle = False

    for item in history_data:
        # Fuel consumption
        fuel = item.get("fuel_level_l")
        if isinstance(fuel, (int, float)) and fuel > 0:
            total_fuel_consumed_l += fuel

        # Distance
        distance = item.get("odometer_km")
        if isinstance(distance, (int, float)) and distance > 0:
            total_distance_km += distance

        # Ambil timestamp terakhir dan status
        timestamp = item.get("timestamp")
        status = item.get("status")
        if timestamp:
            last_timestamp = timestamp
            current_status = status

        # Check for theft alert
        if status == "Theft":
            has_theft_alert = True
        
        # Track idle periods
        # Jika status sekarang adalah "Idle" atau "Start" (awal dari Idle)
        if status in ["Idle", "Start"]:
            if not idle_start_time:  # Catat waktu dimulainya idle
                idle_start_time = timestamp
            idle_end_time = timestamp  # Update waktu terakhir masih idle
            is_currently_idle = True
        elif status in ["Drive", "End"]:
            # Status berubah dari Idle ke Drive/End, jadi idle sudah berakhir
            is_currently_idle = False

    # Kalkulasi idle time dari idle_start_time ke idle_end_time
    # Atau dari idle_start_time ke sekarang jika masih idle
    if idle_start_time and idle_end_time:
        try:
            start_time = datetime.strptime(idle_start_time, "%Y-%m-%d %H:%M:%S")
            
            # Jika masih idle, gunakan waktu sekarang; jika sudah berakhir, gunakan idle_end_time
            if is_currently_idle:
                end_time = datetime.now()
            else:
                end_time = datetime.strptime(idle_end_time, "%Y-%m-%d %H:%M:%S")
            
            time_diff = end_time - start_time
            current_idle_time_mins = time_diff.total_seconds() / 60
        except (ValueError, TypeError):
            current_idle_time_mins = 0.0
    else:
        current_idle_time_mins = 0.0

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
    if current_idle_time_mins > IDLE_TIME_CRITICAL_MINS or has_theft_alert:
        status_color = "🔴 Red (Critical)"
        status_reason = (
            "Idle time > 2 jam" if current_idle_time_mins > IDLE_TIME_CRITICAL_MINS else ""
        )
        if has_theft_alert:
            status_reason += " | Theft alert detected"
        status_reason = status_reason.strip(" |")
    elif current_idle_time_mins > IDLE_TIME_WARNING_MINS:
        status_color = "🟡 Yellow (Warning)"
        status_reason = f"Idle time > 30 menit ({current_idle_time_mins:.1f} menit)"
    else:
        status_color = "🟢 Green (Good)"
        status_reason = "Kondisi baik"

    result = {
        "total_emissions_kg": round(total_emissions_kg, 2),
        "emission_intensity_gco2_km": round(emission_intensity_gco2_km, 2),
        "idle_time_hours": round(current_idle_time_mins / 60, 2),
        "status_color": status_color,
        "status_reason": status_reason,
        "details": {
            "total_fuel_consumed_l": round(total_fuel_consumed_l, 2),
            "total_distance_km": round(total_distance_km, 2),
            "idle_time_minutes": round(current_idle_time_mins, 2),
            "last_status": current_status,
            "last_timestamp": last_timestamp,
            "emission_factor_kgco2_per_liter": DIESEL_EMISSION_FACTOR,
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
        "timestamp": datetime.now().isoformat(),
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
