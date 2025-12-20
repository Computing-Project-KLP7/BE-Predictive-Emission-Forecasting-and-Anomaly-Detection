import joblib
import numpy as np
from pathlib import Path
from typing import Tuple, List
from app.schemas.anomaly import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    DailyAnomalyReportRequest,
    DailyAnomalyReportResponse,
    SeverityLevel
)
from app.core.logging import logger


# Model and parameter paths
MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_ISOLATION_FOREST_PATH = MODEL_DIR / "model_isolation_forest.pkl"
SCALER_ANOMALY_PATH = MODEL_DIR / "scaler_anomaly_detection.pkl"
PARAMS_ANOMALY_PATH = MODEL_DIR / "anomaly_detection_params.pkl"
RESULTS_ANOMALY_PATH = MODEL_DIR / "anomaly_detection_results.pkl"

# Feature order (MUST match training order)
ML_FEATURES = [
    'speed',                    # Kecepatan saat ini (km/h)
    'distance_delta',           # Jarak tempuh sejak record sebelumnya (km)
    'fuel_delta',               # Perubahan fuel level (L)
    'fuel_consumption_rate',    # Konsumsi bahan bakar per km (L/km)
    'idle_duration',            # Durasi idle dalam record ini (menit)
    'rpm',                      # RPM mesin
    'engine_load',              # Beban mesin (0-100%)
    'co2_intensity'             # Intensitas emisi CO2 (g/km)
]

# Default thresholds (dapat dioverride dari file params)
DEFAULT_PARAMS = {
    'fuel_theft_threshold': -5.0,           # Liter
    'excessive_idle_threshold': 120,         # Minutes per day
    'contamination_rate': 0.05              # 5% untuk Isolation Forest
}


class AnomalyModelLoader:
    """Loader untuk anomaly models dan parameters dengan caching"""
    _models_cache = {}
    _scalers_cache = {}
    _params_cache = {}
    
    @classmethod
    def load_model(cls):
        """Load Isolation Forest model dengan caching"""
        if "isolation_forest" not in cls._models_cache:
            cls._models_cache["isolation_forest"] = joblib.load(
                MODEL_ISOLATION_FOREST_PATH
            )
        return cls._models_cache["isolation_forest"]
    
    @classmethod
    def load_scaler(cls):
        """Load scaler dengan caching"""
        if "anomaly" not in cls._scalers_cache:
            cls._scalers_cache["anomaly"] = joblib.load(
                SCALER_ANOMALY_PATH
            )
        return cls._scalers_cache["anomaly"]
    
    @classmethod
    def load_params(cls):
        """Load parameters dengan caching"""
        if "anomaly_params" not in cls._params_cache:
            try:
                params = joblib.load(PARAMS_ANOMALY_PATH)
                cls._params_cache["anomaly_params"] = params
            except FileNotFoundError:
                logger.warning(f"Params file not found, using defaults")
                cls._params_cache["anomaly_params"] = DEFAULT_PARAMS
        return cls._params_cache["anomaly_params"]


def detect_fuel_theft(
    fuel_delta: float,
    speed: float,
    distance_delta: float,
    threshold: float = -5.0
) -> Tuple[bool, float]:
    """
    Deteksi fuel theft menggunakan rule-based approach.
    
    Kriteria:
    - Fuel drop > threshold (default: 5 liter)
    - Kendaraan dalam keadaan diam (speed = 0)
    - Tidak ada pergerakan (distance_delta < 0.1)
    
    Returns:
        Tuple[is_theft_detected, risk_score]
    """
    is_theft = (
        (fuel_delta < threshold) and
        (speed == 0) and
        (distance_delta < 0.1)
    )
    
    # Calculate risk score (0-1)
    if fuel_delta < threshold:
        risk_score = min(abs(fuel_delta) / abs(threshold), 1.0)
    else:
        risk_score = 0.0
    
    return is_theft, risk_score


def detect_emission_inefficiency(
    co2_intensity: float,
    mean: float,
    std: float,
    threshold_multiplier: float = 2.0
) -> bool:
    """
    Deteksi emission inefficiency menggunakan statistical approach.
    
    Kriteria:
    - CO2 intensity > mean + (threshold_multiplier * std)
    - Default threshold_multiplier: 2 (2-sigma rule)
    
    Returns:
        is_inefficient
    """
    if std == 0:
        return False
    
    threshold = mean + (threshold_multiplier * std)
    return co2_intensity > threshold


def calculate_severity(
    fuel_theft: bool,
    excessive_idle: bool,
    emission_inefficiency: bool,
    ml_anomaly: bool,
    ml_score: float,
    fuel_risk: float
) -> SeverityLevel:
    """
    Hitung severity level berdasarkan kombinasi anomali yang terdeteksi.
    
    Rules:
    - CRITICAL: Fuel theft detected
    - HIGH: Multiple anomalies OR strong ML signal
    - MEDIUM: Single anomaly OR weak ML signal
    - LOW: No anomaly but warning signs
    """
    anomaly_count = sum([fuel_theft, excessive_idle, emission_inefficiency, ml_anomaly])
    
    # Critical: Fuel theft is the most critical
    if fuel_theft and fuel_risk > 0.7:
        return SeverityLevel.CRITICAL
    
    # High: Multiple anomalies or strong ML signal
    if anomaly_count >= 2:
        return SeverityLevel.HIGH
    
    if ml_anomaly and ml_score < -0.5:
        return SeverityLevel.HIGH
    
    # Medium: Single anomaly
    if anomaly_count == 1:
        return SeverityLevel.MEDIUM
    
    # Low: Warning signs
    return SeverityLevel.LOW


def detect_anomaly(data: AnomalyDetectionRequest) -> AnomalyDetectionResponse:
    """
    Melakukan deteksi anomali real-time berdasarkan 8 fitur.
    
    Menggunakan kombinasi:
    1. Rule-based: Fuel theft detection
    2. Statistical: Emission inefficiency detection
    3. ML-based: Isolation Forest untuk anomali umum
    4. Rule-based: Excessive idle (memerlukan daily aggregation)
    
    Args:
        data: AnomalyDetectionRequest dengan 8 fitur
        
    Returns:
        AnomalyDetectionResponse dengan deteksi lengkap
        
    Raises:
        Exception: Jika model atau scaler tidak dapat dimuat
    """
    try:
        logger.info(f"Starting anomaly detection...")
        
        # Load models and parameters
        model_if = AnomalyModelLoader.load_model()
        scaler = AnomalyModelLoader.load_scaler()
        params = AnomalyModelLoader.load_params()
        
        logger.info("Models and parameters loaded successfully")
        
        # Prepare features array
        features_dict = {
            'speed': data.speed,
            'distance_delta': data.distance_delta,
            'fuel_delta': data.fuel_delta,
            'fuel_consumption_rate': data.fuel_consumption_rate,
            'idle_duration': data.idle_duration,
            'rpm': data.rpm,
            'engine_load': data.engine_load,
            'co2_intensity': data.co2_intensity
        }
        
        # Create feature array in correct order
        features_array = np.array([[features_dict[col] for col in ML_FEATURES]])
        logger.info(f"Features array shape: {features_array.shape}")
        logger.info(f"Features values: {features_array}")
        
        # Scale features
        features_scaled = scaler.transform(features_array)
        logger.info(f"Scaled features: {features_scaled}")
        
        # ML-based anomaly detection using Isolation Forest
        ml_anomaly_score = model_if.score_samples(features_scaled)[0]
        ml_anomaly_detected = model_if.predict(features_scaled)[0] == -1  # -1 = anomaly
        
        logger.info(f"ML anomaly score: {ml_anomaly_score}, Detected: {ml_anomaly_detected}")
        
        # 1. Fuel Theft Detection (rule-based)
        fuel_theft_threshold = params.get('fuel_theft_threshold', DEFAULT_PARAMS['fuel_theft_threshold'])
        fuel_theft_detected, fuel_risk = detect_fuel_theft(
            fuel_delta=data.fuel_delta,
            speed=data.speed,
            distance_delta=data.distance_delta,
            threshold=fuel_theft_threshold
        )
        logger.info(f"Fuel theft detected: {fuel_theft_detected}, Risk: {fuel_risk}")
        
        # 2. Emission Inefficiency Detection (statistical)
        # Note: Mean and std should come from training data stored in params
        # If not available, we'll estimate or use defaults
        emission_mean = params.get('co2_intensity_mean', 0)
        emission_std = params.get('co2_intensity_std', 1)
        
        emission_inefficiency_detected = detect_emission_inefficiency(
            co2_intensity=data.co2_intensity,
            mean=emission_mean,
            std=emission_std,
            threshold_multiplier=2.0
        )
        logger.info(f"Emission inefficiency detected: {emission_inefficiency_detected}")
        
        # 3. Excessive Idle Detection (requires daily aggregation, not done here)
        # This will be handled by separate daily report endpoint
        excessive_idle_detected = False
        
        # Calculate emission score
        emission_score = min(data.co2_intensity / 1000, 1.0) if data.co2_intensity > 0 else 0.0
        
        # Determine anomaly types
        anomaly_types = []
        if fuel_theft_detected:
            anomaly_types.append("fuel_theft")
        if emission_inefficiency_detected:
            anomaly_types.append("emission_inefficiency")
        if ml_anomaly_detected:
            anomaly_types.append("ml_detected")
        if excessive_idle_detected:
            anomaly_types.append("excessive_idle")
        
        # Is there any anomaly?
        is_anomaly = len(anomaly_types) > 0
        
        # Calculate severity
        severity = calculate_severity(
            fuel_theft=fuel_theft_detected,
            excessive_idle=excessive_idle_detected,
            emission_inefficiency=emission_inefficiency_detected,
            ml_anomaly=ml_anomaly_detected,
            ml_score=ml_anomaly_score,
            fuel_risk=fuel_risk
        )
        
        logger.info(f"Anomaly detected: {is_anomaly}, Severity: {severity}")
        
        # Create response
        response = AnomalyDetectionResponse(
            is_anomaly=is_anomaly,
            anomaly_score=float(ml_anomaly_score),
            anomaly_types=anomaly_types,
            severity=severity,
            fuel_theft_detected=fuel_theft_detected,
            excessive_idle_detected=excessive_idle_detected,
            emission_inefficiency_detected=emission_inefficiency_detected,
            ml_anomaly_detected=ml_anomaly_detected,
            fuel_theft_risk=float(fuel_risk),
            emission_score=float(emission_score)
        )
        
        logger.info("Anomaly detection completed successfully")
        return response
        
    except FileNotFoundError as e:
        logger.error(f"Model or parameter file not found: {e}")
        raise Exception(f"Model atau parameter tidak ditemukan: {str(e)}")
    except Exception as e:
        logger.error(f"Error during anomaly detection: {e}")
        raise Exception(f"Error melakukan deteksi anomali: {str(e)}")


def detect_daily_anomaly(data: DailyAnomalyReportRequest) -> DailyAnomalyReportResponse:
    """
    Deteksi excessive idle untuk laporan harian.
    
    Memerlukan agregasi data harian:
    - Total idle time > 120 menit (2 jam)
    
    Args:
        data: DailyAnomalyReportRequest dengan data agregasi harian
        
    Returns:
        DailyAnomalyReportResponse dengan deteksi excessive idle
    """
    try:
        logger.info(f"Starting daily anomaly detection for device {data.device_id} on {data.date}")
        
        # Load parameters
        params = AnomalyModelLoader.load_params()
        excessive_idle_threshold = params.get(
            'excessive_idle_threshold',
            DEFAULT_PARAMS['excessive_idle_threshold']
        )
        
        # Check excessive idle
        excessive_idle_detected = data.total_idle_minutes > excessive_idle_threshold
        
        # Calculate percentage (assuming 24 hours = 1440 minutes)
        idle_percentage = (data.total_idle_minutes / 1440) * 100
        
        # Warning jika > 80% dari threshold
        is_warning = data.total_idle_minutes > (excessive_idle_threshold * 0.8)
        
        logger.info(f"Device {data.device_id}: Total idle = {data.total_idle_minutes} min, "
                   f"Excessive idle detected: {excessive_idle_detected}")
        
        response = DailyAnomalyReportResponse(
            device_id=data.device_id,
            date=data.date,
            excessive_idle_detected=excessive_idle_detected,
            total_idle_minutes=data.total_idle_minutes,
            excessive_idle_threshold=excessive_idle_threshold,
            idle_percentage=idle_percentage,
            is_warning=is_warning
        )
        
        logger.info("Daily anomaly detection completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error during daily anomaly detection: {e}")
        raise Exception(f"Error melakukan deteksi anomali harian: {str(e)}")
