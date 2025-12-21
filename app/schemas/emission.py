from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EmissionRequest(BaseModel):
    timestamp: datetime
    device_id: int
    odometer_km: float
    fuel_level_L: float
    rpm: int
    ignition_status: bool
    movement_state: str
    battery_voltage: float


class EmissionResponse(BaseModel):
    predicted_emission: float
    unit: str = "gCO2/km"


class EmissionPredictionInput(BaseModel):
    """Schema untuk prediksi emisi berdasarkan aggregated hourly features"""
    speed_mean: float = Field(..., description="Rata-rata kecepatan dalam 1 jam (km/h)", ge=0)
    speed_max: float = Field(..., description="Kecepatan maksimum dalam 1 jam (km/h)", ge=0)
    speed_std: float = Field(default=0, description="Standar deviasi kecepatan dalam 1 jam", ge=0)
    distance_delta_total: float = Field(..., description="Total jarak tempuh dalam 1 jam (km)", ge=0)
    rpm_mean: float = Field(..., description="Rata-rata RPM dalam 1 jam", ge=0)
    rpm_max: float = Field(..., description="RPM maksimum dalam 1 jam", ge=0)
    engine_load_mean: float = Field(..., description="Rata-rata engine load dalam 1 jam (%)", ge=0, le=100)
    is_moving_mean: float = Field(..., description="Proporsi waktu bergerak dalam 1 jam (0-1)", ge=0, le=1)
    is_idle_total: float = Field(default=0, description="Total durasi idle dalam 1 jam (menit)", ge=0, le=60)
    hour: int = Field(..., description="Jam dalam sehari (0-23)", ge=0, le=23)
    day_of_week: int = Field(..., description="Hari dalam seminggu (0-6)", ge=0, le=6)
    is_weekend: int = Field(..., description="Apakah hari weekend (0/1)", ge=0, le=1)


class EmissionPredictionOutput(BaseModel):
    """Schema untuk output prediksi emisi"""
    co2_emissions_grams: float = Field(..., description="Prediksi emisi CO2 (grams per hour)")
    co2_intensity: float = Field(..., description="Prediksi CO2 intensity (g/km)")
    predictions: dict = Field(default_factory=dict, description="Detail prediksi dari kedua model")