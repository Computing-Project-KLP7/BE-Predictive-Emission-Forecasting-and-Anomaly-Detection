from pydantic import BaseModel
from typing import List
from enum import Enum


class SeverityLevel(str, Enum):
    """Severity levels untuk anomaly detection"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyDetectionRequest(BaseModel):
    """
    Request schema untuk deteksi anomali real-time (per record).
    Semua fitur adalah hasil kalkulasi dari satu record raw data.
    """
    speed: float                    # Kecepatan saat ini (km/h) - 0-200
    distance_delta: float           # Jarak sejak record sebelumnya (km) - 0-200
    fuel_delta: float               # Perubahan fuel level (L) - negatif = konsumsi, -50 to +50
    fuel_consumption_rate: float    # Konsumsi bahan bakar per km (L/km) - 0-2
    idle_duration: float            # Durasi idle record ini (menit) - 0-1440
    rpm: float                      # RPM mesin - 0-3000
    engine_load: float              # Beban mesin (%) - 0-100
    co2_intensity: float            # Intensitas emisi CO2 (g/km) - 0-1000


class AnomalyDetectionResponse(BaseModel):
    """
    Response schema untuk anomaly detection.
    Mengembalikan hasil deteksi 4 jenis anomali + severity level.
    """
    is_anomaly: bool                # Ada anomali atau tidak
    anomaly_score: float            # Score dari Isolation Forest (-1 to 1)
    anomaly_types: List[str]        # Jenis-jenis anomali yang terdeteksi
    severity: SeverityLevel         # Level severity: LOW, MEDIUM, HIGH, CRITICAL
    
    # Individual flags
    fuel_theft_detected: bool       # Deteksi: Fuel theft (rule-based)
    excessive_idle_detected: bool   # Deteksi: Excessive idle (rule-based)
    emission_inefficiency_detected: bool  # Deteksi: Emission inefficiency (statistical)
    ml_anomaly_detected: bool       # Deteksi: ML-based anomaly (Isolation Forest)
    
    # Detailed info
    fuel_theft_risk: float          # Risk score untuk fuel theft (0-1)
    emission_score: float           # Emission intensity score (0-1)


class DailyAnomalyReportRequest(BaseModel):
    """
    Request schema untuk daily anomaly report.
    Untuk deteksi excessive idle yang memerlukan agregasi harian.
    """
    device_id: int                  # ID perangkat
    date: str                       # Tanggal dalam format YYYY-MM-DD
    total_idle_minutes: float       # Total idle dalam 1 hari (menit)
    average_co2_intensity: float    # Rata-rata CO2 intensity hari ini


class DailyAnomalyReportResponse(BaseModel):
    """
    Response schema untuk daily anomaly report.
    """
    device_id: int
    date: str
    excessive_idle_detected: bool   # Apakah excessive idle terdeteksi
    total_idle_minutes: float       # Total idle yang dilaporkan
    excessive_idle_threshold: float # Threshold yang digunakan (120 menit)
    idle_percentage: float          # Persentase idle time (0-100)
    is_warning: bool                # Warning jika mendekati threshold
