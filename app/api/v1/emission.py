from fastapi import APIRouter, HTTPException
from app.schemas.emission import (
    EmissionRequest, 
    EmissionResponse, 
    EmissionPredictionInput, 
    EmissionPredictionOutput
)
from app.services.emission_service import predict_emission, get_model_info


router = APIRouter()


# @router.post("/predict", response_model=EmissionResponse)
# def predict(data: EmissionRequest):
#     # result = predict_emission(data)
#     return ()


@router.post("/predict-hourly", response_model=EmissionPredictionOutput)
async def predict_hourly_emission(data: EmissionPredictionInput):
    """
    Prediksi emisi CO2 berdasarkan aggregated hourly features.
    
    Endpoint ini menerima 12 features yang sudah diagregasi per jam dan melakukan prediksi
    untuk CO2 emissions (grams per hour) dan CO2 intensity (g/km).
    
    ### Features Required:
    - **speed_mean**: Rata-rata kecepatan dalam 1 jam (km/h)
    - **speed_max**: Kecepatan maksimum dalam 1 jam (km/h)
    - **speed_std**: Standar deviasi kecepatan dalam 1 jam
    - **distance_delta_total**: Total jarak tempuh dalam 1 jam (km)
    - **rpm_mean**: Rata-rata RPM dalam 1 jam
    - **rpm_max**: RPM maksimum dalam 1 jam
    - **engine_load_mean**: Rata-rata engine load dalam 1 jam (%)
    - **is_moving_mean**: Proporsi waktu bergerak dalam 1 jam (0-1)
    - **is_idle_total**: Total durasi idle dalam 1 jam (menit)
    - **hour**: Jam dalam sehari (0-23)
    - **day_of_week**: Hari dalam seminggu (0-6)
    - **is_weekend**: Apakah hari weekend (0/1)
    
    ### Example Request:
    ```json
    {
        "speed_mean": 45.5,
        "speed_max": 80.0,
        "speed_std": 15.2,
        "distance_delta_total": 50.0,
        "rpm_mean": 1500,
        "rpm_max": 2500,
        "engine_load_mean": 45.0,
        "is_moving_mean": 0.85,
        "is_idle_total": 9,
        "hour": 14,
        "day_of_week": 2,
        "is_weekend": 0
    }
    ```
    """
    try:
        result = predict_emission(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-info")
async def get_emission_model_info():
    """
    Get informasi tentang model emission prediction yang sedang digunakan.
    """
    try:
        info = get_model_info()
        return {
            "status": "success",
            "model_info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))