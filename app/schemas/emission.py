from pydantic import BaseModel
from datetime import datetime


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


class EmissionPredictionRequest(BaseModel):
    """
    Request schema untuk prediksi emisi berdasarkan fitur agregasi per jam.
    Semua fitur adalah hasil agregasi data selama 1 jam.
    """
    speed_mean: float                # Rata-rata kecepatan dalam 1 jam (km/h)
    speed_max: float                 # Kecepatan maksimum dalam 1 jam (km/h)
    speed_std: float                 # Standar deviasi kecepatan dalam 1 jam
    distance_delta_total: float      # Total jarak tempuh dalam 1 jam (km)
    rpm_mean: float                  # Rata-rata RPM dalam 1 jam
    rpm_max: float                   # RPM maksimum dalam 1 jam
    engine_load_mean: float          # Rata-rata engine load dalam 1 jam (%)
    is_moving_mean: float            # Proporsi waktu bergerak dalam 1 jam (0-1)
    is_idle_total: float             # Total durasi idle dalam 1 jam (menit)
    hour: int                        # Jam dalam sehari (0-23)
    day_of_week: int                 # Hari dalam seminggu (0-6, 0=Senin)
    is_weekend: int                  # Apakah hari weekend (0/1)


class EmissionPredictionResponse(BaseModel):
    """
    Response schema untuk prediksi emisi.
    Mengembalikan prediksi CO2 emissions dan CO2 intensity.
    """
    co2_grams_total: float           # Prediksi total CO2 dalam gram per jam
    co2_intensity_mean: float        # Prediksi CO2 intensity dalam g/km
    unit_emissions: str = "grams/hour"
    unit_intensity: str = "g/km"