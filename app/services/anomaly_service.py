import pickle
import numpy as np
import os
from typing import Dict, Any, List, Tuple
from app.schemas.anomaly import (
    AnomalyDetectionInput,
    AnomalyDetectionOutput,
    SeverityLevel,
    FuelTheftDetectionInput,
    FuelTheftDetectionOutput,
    ExcessiveIdleDetectionInput,
    ExcessiveIdleDetectionOutput,
    EmissionInefficientDetectionInput,
    EmissionInefficientDetectionOutput
)

# Try to import joblib as alternative
try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

# Path ke model files
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models', 'anomaly')

# Cache untuk loaded models
_models_cache = {}

# Default thresholds
DEFAULT_THRESHOLDS = {
    'fuel_theft_threshold': -5.0,           # Liter
    'excessive_idle_threshold': 120,         # Minutes per day
    'contamination_rate': 0.05              # 5% untuk Isolation Forest
}


def load_model(filename: str):
    """Load model dari pickle file dengan caching dan compatibility handling"""
    if filename in _models_cache:
        return _models_cache[filename]
    
    filepath = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found: {filepath}")
    
    try:
        # Try joblib first (better for sklearn models)
        if HAS_JOBLIB:
            try:
                model = joblib.load(filepath)
                _models_cache[filename] = model
                return model
            except Exception as e:
                pass  # Fall through to pickle
        
        # Try standard pickle load
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        
    except Exception as e:
        # Try with latin1 encoding for older Python 2 pickles
        try:
            with open(filepath, 'rb') as f:
                model = pickle.load(f, encoding='latin1')
        except Exception as e2:
            raise Exception(f"Failed to load {filename}. Error: {str(e)}")
    
    _models_cache[filename] = model
    return model


def get_anomaly_params() -> Dict[str, Any]:
    """Get anomaly detection parameters"""
    try:
        params = load_model('anomaly_detection_params.pkl')
        return params
    except Exception as e:
        # Return default if file not found
        return DEFAULT_THRESHOLDS


def detect_fuel_theft(input_data: FuelTheftDetectionInput) -> Tuple[bool, Dict[str, Any]]:
    """
    Deteksi fuel theft berdasarkan rule-based criteria
    
    Kriteria:
    - Fuel delta < -5 liter (drop besar)
    - Speed = 0 (kendaraan diam)
    - Distance delta < 0.1 km (tidak ada pergerakan)
    """
    params = get_anomaly_params()
    fuel_theft_threshold = params.get('fuel_theft_threshold', DEFAULT_THRESHOLDS['fuel_theft_threshold'])
    
    # Check criteria
    large_fuel_drop = input_data.fuel_delta < fuel_theft_threshold
    vehicle_stationary = input_data.speed == 0
    no_movement = input_data.distance_delta < 0.1
    
    is_fuel_theft = large_fuel_drop and vehicle_stationary and no_movement
    
    # Calculate risk score (0-1)
    if large_fuel_drop:
        # Normalize fuel drop relative to threshold
        risk_score = min(1.0, abs(input_data.fuel_delta) / abs(fuel_theft_threshold))
    else:
        risk_score = 0.0
    
    details = {
        'large_fuel_drop': bool(large_fuel_drop),
        'vehicle_stationary': bool(vehicle_stationary),
        'no_movement': bool(no_movement),
        'fuel_delta': float(input_data.fuel_delta),
        'speed': float(input_data.speed),
        'distance_delta': float(input_data.distance_delta)
    }
    
    reason = ""
    if is_fuel_theft:
        reason = f"Fuel theft detected: Large fuel drop ({input_data.fuel_delta}L) while stationary"
    elif large_fuel_drop and not vehicle_stationary:
        reason = f"Suspicious fuel drop ({input_data.fuel_delta}L) while moving"
    elif large_fuel_drop:
        reason = f"Fuel drop detected ({input_data.fuel_delta}L) - monitoring required"
    else:
        reason = "Normal fuel consumption"
    
    return is_fuel_theft, {'details': details, 'reason': reason, 'risk_score': risk_score}


def detect_excessive_idle(input_data: ExcessiveIdleDetectionInput) -> Tuple[bool, Dict[str, Any]]:
    """
    Deteksi excessive idle time per hari
    
    Kriteria: total idle per hari > 120 menit (2 jam)
    """
    params = get_anomaly_params()
    excessive_idle_threshold = params.get('excessive_idle_threshold', DEFAULT_THRESHOLDS['excessive_idle_threshold'])
    
    is_excessive = input_data.idle_duration_daily > excessive_idle_threshold
    excess_time = max(0, input_data.idle_duration_daily - excessive_idle_threshold)
    
    details = {
        'idle_duration_daily': float(input_data.idle_duration_daily),
        'threshold': float(excessive_idle_threshold),
        'excess_time': float(excess_time),
        'is_excessive': bool(is_excessive)
    }
    
    reason = ""
    if is_excessive:
        reason = f"Excessive idle detected: {input_data.idle_duration_daily}min > {excessive_idle_threshold}min threshold"
    else:
        reason = f"Normal idle time: {input_data.idle_duration_daily}min"
    
    return is_excessive, {'details': details, 'reason': reason}


def detect_emission_inefficiency(input_data: EmissionInefficientDetectionInput,
                                 co2_mean: float = None,
                                 co2_std: float = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Deteksi emission inefficiency berdasarkan statistical method
    
    Kriteria: CO2 intensity > mean + (2 * std)
    """
    # Use provided or estimate from input
    if co2_mean is None:
        co2_mean = input_data.co2_intensity_mean or 150.0  # Default estimate
    if co2_std is None:
        co2_std = input_data.co2_intensity_std or 50.0  # Default estimate
    
    threshold = co2_mean + (2 * co2_std)
    is_inefficient = input_data.co2_intensity > threshold
    
    # Calculate deviation in terms of std dev
    deviation = (input_data.co2_intensity - co2_mean) / co2_std if co2_std > 0 else 0
    
    # Approximate percentile (using z-score to percentile conversion)
    from scipy import stats
    try:
        percentile = stats.norm.cdf(deviation) * 100
    except:
        percentile = 50.0
    
    details = {
        'co2_intensity': float(input_data.co2_intensity),
        'threshold': float(threshold),
        'mean': float(co2_mean),
        'std': float(co2_std),
        'deviation': float(deviation),
        'percentile': float(percentile)
    }
    
    reason = ""
    if is_inefficient:
        reason = f"Inefficient emission detected: CO2 intensity {input_data.co2_intensity:.2f} > threshold {threshold:.2f}"
    else:
        reason = f"Normal emission level: CO2 intensity {input_data.co2_intensity:.2f}"
    
    return is_inefficient, {'details': details, 'reason': reason}


def predict_ml_anomaly(input_data: AnomalyDetectionInput) -> Tuple[float, bool]:
    """
    Prediksi anomali menggunakan Isolation Forest model
    
    Returns:
        anomaly_score: Score dari -1 (pasti anomali) hingga 1 (pasti normal)
        is_anomaly: Boolean flag berdasarkan score threshold
    """
    try:
        # Load model dan scaler
        model_if = load_model('model_isolation_forest.pkl')
        scaler = load_model('scaler_anomaly_detection.pkl')
        
        # Feature list sesuai urutan saat training
        feature_cols = [
            'speed',
            'distance_delta',
            'fuel_delta',
            'fuel_consumption_rate',
            'idle_duration',
            'rpm',
            'engine_load',
            'co2_intensity'
        ]
        
        # Ekstrak features dari input data
        features = np.array([[
            input_data.speed,
            input_data.distance_delta,
            input_data.fuel_delta,
            input_data.fuel_consumption_rate,
            input_data.idle_duration,
            input_data.rpm,
            input_data.engine_load,
            input_data.co2_intensity
        ]])
        
        # Scale features
        features_scaled = scaler.transform(features)
        
        # Get anomaly score (-1 untuk anomali, 1 untuk normal)
        anomaly_score = model_if.score_samples(features_scaled)[0]
        
        # Get prediction (-1 untuk anomali, 1 untuk normal)
        prediction = model_if.predict(features_scaled)[0]
        is_anomaly_ml = prediction == -1
        
        return anomaly_score, is_anomaly_ml
    
    except Exception as e:
        # Jika model tidak bisa di-load, return neutral score
        return 0.0, False


def calculate_severity(anomaly_types: List[str], anomaly_score: float, confidence: float) -> Tuple[SeverityLevel, float]:
    """
    Calculate severity level berdasarkan anomaly types dan scores
    """
    if not anomaly_types:
        return SeverityLevel.LOW, 0.0
    
    # Base severity based on anomaly types
    severity_map = {
        'fuel_theft': 0.95,          # CRITICAL
        'ml_detected': 0.7,          # HIGH
        'excessive_idle': 0.5,       # MEDIUM
        'emission_inefficient': 0.4  # LOW to MEDIUM
    }
    
    # Get max severity from detected anomalies
    max_severity_score = max([severity_map.get(t, 0.3) for t in anomaly_types])
    
    # Adjust by anomaly score (more negative = more anomalous)
    if anomaly_score < -0.5:
        max_severity_score = min(1.0, max_severity_score + 0.2)
    
    # Map to severity level
    if max_severity_score >= 0.85:
        severity = SeverityLevel.CRITICAL
    elif max_severity_score >= 0.65:
        severity = SeverityLevel.HIGH
    elif max_severity_score >= 0.4:
        severity = SeverityLevel.MEDIUM
    else:
        severity = SeverityLevel.LOW
    
    return severity, min(1.0, max_severity_score * confidence)


def predict_anomaly(input_data: AnomalyDetectionInput) -> AnomalyDetectionOutput:
    """
    Main function untuk prediksi anomali menggunakan kombinasi rule-based dan ML approaches
    """
    try:
        anomaly_types = []
        details = {}
        
        # 1. Fuel Theft Detection
        fuel_theft_input = FuelTheftDetectionInput(
            speed=input_data.speed,
            distance_delta=input_data.distance_delta,
            fuel_delta=input_data.fuel_delta
        )
        is_fuel_theft, fuel_theft_details = detect_fuel_theft(fuel_theft_input)
        if is_fuel_theft:
            anomaly_types.append('fuel_theft')
        details['fuel_theft'] = fuel_theft_details
        
        # 2. ML-Based Anomaly Detection
        anomaly_score, is_anomaly_ml = predict_ml_anomaly(input_data)
        if is_anomaly_ml:
            anomaly_types.append('ml_detected')
        details['ml_anomaly'] = {
            'anomaly_score': float(anomaly_score),
            'is_anomaly_ml': bool(is_anomaly_ml)
        }
        
        # 3. Emission Inefficiency Detection
        emission_inefficient_input = EmissionInefficientDetectionInput(
            co2_intensity=input_data.co2_intensity
        )
        is_inefficient, emission_details = detect_emission_inefficiency(emission_inefficient_input)
        if is_inefficient:
            anomaly_types.append('emission_inefficient')
        details['emission_inefficiency'] = emission_details
        
        # Calculate overall anomaly and confidence
        is_anomaly = len(anomaly_types) > 0
        
        # Confidence calculation based on number of detections
        confidence = min(1.0, len(anomaly_types) / 3.0)  # Max 3 detection methods
        if anomaly_score < -0.3:
            confidence = min(1.0, confidence + 0.3)
        confidence = max(0.3, confidence)  # Minimum confidence 0.3
        
        # Calculate severity
        severity, severity_score = calculate_severity(anomaly_types, anomaly_score, confidence)
        
        return AnomalyDetectionOutput(
            is_anomaly=is_anomaly,
            anomaly_score=round(anomaly_score, 4),
            anomaly_types=anomaly_types,
            severity=severity,
            details=details,
            confidence=round(confidence, 2)
        )
    
    except Exception as e:
        raise Exception(f"Anomaly prediction error: {str(e)}")


def get_anomaly_model_info() -> Dict[str, Any]:
    """Get model information"""
    try:
        params = get_anomaly_params()
        return {
            "status": "success",
            "parameters": params,
            "features": [
                'speed', 'distance_delta', 'fuel_delta', 'fuel_consumption_rate',
                'idle_duration', 'rpm', 'engine_load', 'co2_intensity'
            ],
            "anomaly_types": ['fuel_theft', 'ml_detected', 'emission_inefficient'],
            "severity_levels": [s.value for s in SeverityLevel]
        }
    except Exception as e:
        return {"error": str(e), "status": "Model info not available"}
