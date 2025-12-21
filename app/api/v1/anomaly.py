from fastapi import APIRouter, HTTPException
from app.schemas.anomaly import (
    AnomalyDetectionInput,
    AnomalyDetectionOutput,
    FuelTheftDetectionInput,
    FuelTheftDetectionOutput,
    ExcessiveIdleDetectionInput,
    ExcessiveIdleDetectionOutput,
    EmissionInefficientDetectionInput,
    EmissionInefficientDetectionOutput
)
from app.services.anomaly_service import (
    predict_anomaly,
    detect_fuel_theft,
    detect_excessive_idle,
    detect_emission_inefficiency,
    get_anomaly_model_info
)


router = APIRouter()


@router.post("/detect", response_model=AnomalyDetectionOutput)
async def detect_anomaly(data: AnomalyDetectionInput):
    """
    Real-time anomaly detection menggunakan kombinasi rule-based dan ML approaches.
    
    Mendeteksi 3 jenis anomali:
    1. **Fuel Theft**: Drop fuel > 5L saat kendaraan diam dan tidak bergerak
    2. **ML-Based Anomaly**: Menggunakan Isolation Forest pada 8 features
    3. **Emission Inefficiency**: CO2 intensity > mean + 2*std
    
    ### Features Required (8 features):
    - **speed**: Kecepatan saat ini (km/h)
    - **distance_delta**: Jarak sejak record sebelumnya (km)
    - **fuel_delta**: Perubahan fuel level (L), negatif = konsumsi
    - **fuel_consumption_rate**: Konsumsi per km (L/km)
    - **idle_duration**: Durasi idle record ini (menit)
    - **rpm**: RPM mesin
    - **engine_load**: Beban mesin (0-100%)
    - **co2_intensity**: Intensitas CO2 (g/km)
    
    ### Example Request (Fuel Theft Suspect):
    ```json
    {
        "speed": 0,
        "distance_delta": 0,
        "fuel_delta": -10.0,
        "fuel_consumption_rate": 0,
        "idle_duration": 5,
        "rpm": 0,
        "engine_load": 0,
        "co2_intensity": 0
    }
    ```
    
    ### Response:
    ```json
    {
        "is_anomaly": true,
        "anomaly_score": -0.234,
        "anomaly_types": ["fuel_theft"],
        "severity": "HIGH",
        "details": {...},
        "confidence": 0.95
    }
    ```
    """
    try:
        result = predict_anomaly(data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-fuel-theft", response_model=FuelTheftDetectionOutput)
async def detect_fuel_theft_endpoint(data: FuelTheftDetectionInput):
    """
    Deteksi fuel theft dengan rule-based criteria.
    
    Kriteria Fuel Theft:
    - Fuel drop > 5 liter
    - Kendaraan diam (speed = 0)
    - Tidak ada pergerakan (distance_delta < 0.1 km)
    
    ### Example Request:
    ```json
    {
        "speed": 0,
        "distance_delta": 0.05,
        "fuel_delta": -8.5
    }
    ```
    """
    try:
        is_fuel_theft, details = detect_fuel_theft(data)
        
        return FuelTheftDetectionOutput(
            is_fuel_theft=is_fuel_theft,
            fuel_delta=data.fuel_delta,
            risk_score=details['risk_score'],
            reason=details['reason']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-excessive-idle", response_model=ExcessiveIdleDetectionOutput)
async def detect_excessive_idle_endpoint(data: ExcessiveIdleDetectionInput):
    """
    Deteksi excessive idle time per hari.
    
    Kriteria: Total idle time per hari > 120 menit (2 jam)
    
    ### Example Request:
    ```json
    {
        "idle_duration_daily": 180,
        "device_id": "device_123"
    }
    ```
    """
    try:
        is_excessive, details = detect_excessive_idle(data)
        
        return ExcessiveIdleDetectionOutput(
            is_excessive_idle=is_excessive,
            idle_duration_daily=data.idle_duration_daily,
            threshold=details['details']['threshold'],
            excess_time=details['details']['excess_time']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-emission-inefficiency", response_model=EmissionInefficientDetectionOutput)
async def detect_emission_inefficiency_endpoint(data: EmissionInefficientDetectionInput):
    """
    Deteksi emission inefficiency menggunakan statistical method.
    
    Kriteria: CO2 intensity > mean + (2 * std)
    
    ### Example Request:
    ```json
    {
        "co2_intensity": 450.5,
        "co2_intensity_mean": 150.0,
        "co2_intensity_std": 50.0
    }
    ```
    """
    try:
        is_inefficient, details = detect_emission_inefficiency(
            data,
            co2_mean=data.co2_intensity_mean,
            co2_std=data.co2_intensity_std
        )
        
        detail_info = details['details']
        
        return EmissionInefficientDetectionOutput(
            is_inefficient=is_inefficient,
            co2_intensity=data.co2_intensity,
            threshold=detail_info['threshold'],
            deviation=detail_info['deviation'],
            percentile=detail_info['percentile']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/model-info")
async def get_anomaly_model_info_endpoint():
    """
    Get informasi tentang model anomaly detection yang sedang digunakan.
    """
    try:
        info = get_anomaly_model_info()
        return {
            "status": "success",
            "model_info": info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))