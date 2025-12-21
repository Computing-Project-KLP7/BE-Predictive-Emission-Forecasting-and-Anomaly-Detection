from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class SeverityLevel(str, Enum):
    """Enum untuk severity level anomali"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AnomalyDetectionInput(BaseModel):
    """Schema untuk real-time anomaly detection based on raw data"""
    speed: float = Field(..., description="Kecepatan saat ini (km/h)", ge=0)
    distance_delta: float = Field(..., description="Jarak tempuh sejak record sebelumnya (km)", ge=0)
    fuel_delta: float = Field(..., description="Perubahan fuel level (L) - negatif = konsumsi")
    fuel_consumption_rate: float = Field(default=0, description="Konsumsi bahan bakar per km (L/km)", ge=0)
    idle_duration: float = Field(default=0, description="Durasi idle dalam record ini (menit)", ge=0)
    rpm: float = Field(..., description="RPM mesin", ge=0)
    engine_load: float = Field(..., description="Beban mesin (0-100%)", ge=0, le=100)
    co2_intensity: float = Field(..., description="Intensitas emisi CO2 (g/km)", ge=0)


class AnomalyDetectionOutput(BaseModel):
    """Schema untuk output anomaly detection"""
    is_anomaly: bool = Field(..., description="Apakah record dianggap anomali")
    anomaly_score: float = Field(..., description="Anomaly score dari Isolation Forest (-1 to 1)")
    anomaly_types: List[str] = Field(default_factory=list, description="Tipe-tipe anomali yang terdeteksi")
    severity: SeverityLevel = Field(..., description="Tingkat severity anomali")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detail masing-masing deteksi")
    confidence: float = Field(..., description="Confidence score (0-1)")


class FuelTheftDetectionInput(BaseModel):
    """Schema untuk fuel theft detection"""
    speed: float = Field(..., description="Kecepatan saat ini (km/h)", ge=0)
    distance_delta: float = Field(..., description="Jarak tempuh (km)", ge=0)
    fuel_delta: float = Field(..., description="Perubahan fuel level (L)")


class FuelTheftDetectionOutput(BaseModel):
    """Schema untuk output fuel theft detection"""
    is_fuel_theft: bool = Field(..., description="Apakah terdeteksi fuel theft")
    fuel_delta: float = Field(..., description="Fuel delta value")
    risk_score: float = Field(..., description="Risk score (0-1)")
    reason: str = Field(..., description="Penjelasan deteksi")


class ExcessiveIdleDetectionInput(BaseModel):
    """Schema untuk excessive idle detection"""
    idle_duration_daily: float = Field(..., description="Total durasi idle per hari (menit)", ge=0)
    device_id: Optional[str] = Field(default=None, description="Device ID untuk tracking historis")


class ExcessiveIdleDetectionOutput(BaseModel):
    """Schema untuk output excessive idle detection"""
    is_excessive_idle: bool = Field(..., description="Apakah idle time berlebihan")
    idle_duration_daily: float = Field(..., description="Total idle per hari (menit)")
    threshold: float = Field(..., description="Threshold yang digunakan (menit)")
    excess_time: float = Field(..., description="Selisih dari threshold (menit)")


class EmissionInefficientDetectionInput(BaseModel):
    """Schema untuk emission inefficiency detection"""
    co2_intensity: float = Field(..., description="CO2 intensity value (g/km)", ge=0)
    co2_intensity_mean: Optional[float] = Field(default=None, description="Mean CO2 intensity dari populasi")
    co2_intensity_std: Optional[float] = Field(default=None, description="Std dev CO2 intensity dari populasi")


class EmissionInefficientDetectionOutput(BaseModel):
    """Schema untuk output emission inefficiency detection"""
    is_inefficient: bool = Field(..., description="Apakah emisi tidak efisien")
    co2_intensity: float = Field(..., description="CO2 intensity value")
    threshold: float = Field(..., description="Threshold yang digunakan")
    deviation: float = Field(..., description="Deviasi dari mean (dalam std dev units)")
    percentile: float = Field(..., description="Percentile dari data (0-100)")
