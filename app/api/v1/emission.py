from fastapi import APIRouter, HTTPException
from app.schemas.emission import (
    EmissionRequest,
    EmissionResponse,
    EmissionPredictionRequest,
    EmissionPredictionResponse
)
from app.services.emission_service import predict_emission
from app.core.logging import logger


router = APIRouter()


# @router.post("/predict", response_model=EmissionResponse)
# def predict(data: EmissionRequest):
#     # result = predict_emission(data)
#     return ()


@router.post("/predict-hourly", response_model=EmissionPredictionResponse)
def predict_hourly(data: EmissionPredictionRequest):
    """
    Endpoint untuk memprediksi emisi CO2 berdasarkan fitur agregasi per jam.
    
    Menerima 12 fitur yang sudah diagregasi per jam dan mengembalikan prediksi:
    - CO2 Emissions (grams per hour)
    - CO2 Intensity (g/km)
    
    Args:
        data: EmissionPredictionRequest dengan fitur-fitur:
            - speed_mean: Rata-rata kecepatan (km/h)
            - speed_max: Kecepatan maksimum (km/h)
            - speed_std: Standar deviasi kecepatan
            - distance_delta_total: Total jarak tempuh (km)
            - rpm_mean: Rata-rata RPM
            - rpm_max: RPM maksimum
            - engine_load_mean: Rata-rata engine load (%)
            - is_moving_mean: Proporsi waktu bergerak (0-1)
            - is_idle_total: Total durasi idle (menit)
            - hour: Jam dalam sehari (0-23)
            - day_of_week: Hari dalam seminggu (0-6)
            - is_weekend: Flag akhir pekan (0/1)
    
    Returns:
        EmissionPredictionResponse dengan:
            - co2_grams_total: Prediksi emisi dalam gram/jam
            - co2_intensity_mean: Prediksi intensitas emisi dalam g/km
    """
    try:
        logger.info(f"Received prediction request: {data}")
        result = predict_emission(data)
        return result
    except Exception as e:
        logger.error(f"Error in predict_hourly endpoint: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))