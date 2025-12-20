from fastapi import APIRouter, HTTPException
from app.schemas.anomaly import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    DailyAnomalyReportRequest,
    DailyAnomalyReportResponse
)
from app.services.anomaly_service import detect_anomaly, detect_daily_anomaly
from app.core.logging import logger


router = APIRouter()


@router.post("/detect", response_model=AnomalyDetectionResponse)
def detect(data: AnomalyDetectionRequest):
    """
    Endpoint untuk deteksi anomali real-time (per record).
    
    Mendeteksi 4 jenis anomali:
    1. Fuel Theft - Rule-based detection
    2. Excessive Idle - Agregasi harian (tidak terdeteksi di sini)
    3. Emission Inefficiency - Statistical detection
    4. ML-based Anomaly - Isolation Forest
    
    Args:
        data: AnomalyDetectionRequest dengan 8 fitur:
            - speed: Kecepatan saat ini (km/h)
            - distance_delta: Jarak sejak record sebelumnya (km)
            - fuel_delta: Perubahan fuel level (L)
            - fuel_consumption_rate: Konsumsi per km (L/km)
            - idle_duration: Durasi idle (menit)
            - rpm: RPM mesin
            - engine_load: Beban mesin (%)
            - co2_intensity: Intensitas emisi (g/km)
    
    Returns:
        AnomalyDetectionResponse dengan:
            - is_anomaly: Ada anomali atau tidak
            - anomaly_score: Score dari Isolation Forest (-1 to 1)
            - anomaly_types: List jenis anomali terdeteksi
            - severity: Level severity (LOW, MEDIUM, HIGH, CRITICAL)
            - Detailed flags dan scores untuk setiap jenis anomali
    """
    try:
        logger.info(f"Received anomaly detection request: {data}")
        result = detect_anomaly(data)
        return result
    except Exception as e:
        logger.error(f"Error in detect endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/daily-report", response_model=DailyAnomalyReportResponse)
def daily_anomaly_report(data: DailyAnomalyReportRequest):
    """
    Endpoint untuk laporan anomali harian.
    
    Digunakan untuk deteksi excessive idle yang memerlukan agregasi per hari.
    Threshold default: 120 menit (2 jam) per hari.
    
    Args:
        data: DailyAnomalyReportRequest dengan:
            - device_id: ID perangkat
            - date: Tanggal (YYYY-MM-DD)
            - total_idle_minutes: Total idle dalam 1 hari (menit)
            - average_co2_intensity: Rata-rata CO2 intensity (g/km)
    
    Returns:
        DailyAnomalyReportResponse dengan:
            - excessive_idle_detected: Ada excessive idle atau tidak
            - idle_percentage: Persentase idle time (0-100)
            - is_warning: Warning jika mendekati threshold
    """
    try:
        logger.info(f"Received daily anomaly report request: {data}")
        result = detect_daily_anomaly(data)
        return result
    except Exception as e:
        logger.error(f"Error in daily_anomaly_report endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))