import pickle
import numpy as np
import os
import sys
from typing import Dict, Any
from app.schemas.emission import EmissionPredictionInput, EmissionPredictionOutput

# Try to import joblib as alternative
try:
    import joblib
    HAS_JOBLIB = True
except ImportError:
    HAS_JOBLIB = False

# Path ke model files
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models', 'emission')

# Cache untuk loaded models
_models_cache = {}


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
        
        # Try standard pickle load with protocol 4
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        
    except Exception as e:
        # Try with latin1 encoding for older Python 2 pickles
        try:
            with open(filepath, 'rb') as f:
                model = pickle.load(f, encoding='latin1')
        except Exception as e2:
            # Try with bytes encoding
            try:
                with open(filepath, 'rb') as f:
                    model = pickle.load(f, encoding='bytes')
            except Exception as e3:
                raise Exception(f"Failed to load {filename}. Tried joblib, pickle, latin1, bytes encodings. Error: {str(e)}")
    
    _models_cache[filename] = model
    return model


def get_model_info() -> Dict[str, Any]:
    """Get model information"""
    try:
        info = load_model('emission_model_info.pkl')
        return info
    except Exception as e:
        return {"error": str(e), "status": "Model info not available"}


def predict_emission(input_data: EmissionPredictionInput) -> EmissionPredictionOutput:
    """
    Prediksi emisi CO2 berdasarkan hourly aggregated features
    
    Args:
        input_data: EmissionPredictionInput dengan 12 features
    
    Returns:
        EmissionPredictionOutput dengan prediksi CO2 emissions dan intensity
    """
    try:
        # Load models dan scalers
        model_co2_emissions = load_model('model_co2_emissions.pkl')
        model_co2_intensity = load_model('model_co2_intensity.pkl')
        scaler_co2_emissions = load_model('scaler_co2_emissions.pkl')
        scaler_co2_intensity = load_model('scaler_co2_intensity.pkl')
        
        # Feature list sesuai urutan saat training
        feature_cols = [
            'speed_mean',
            'speed_max',
            'speed_std',
            'distance_delta_total',
            'rpm_mean',
            'rpm_max',
            'engine_load_mean',
            'is_moving_mean',
            'is_idle_total',
            'hour',
            'day_of_week',
            'is_weekend'
        ]
        
        # Ekstrak features dari input data
        features = np.array([[
            input_data.speed_mean,
            input_data.speed_max,
            input_data.speed_std,
            input_data.distance_delta_total,
            input_data.rpm_mean,
            input_data.rpm_max,
            input_data.engine_load_mean,
            input_data.is_moving_mean,
            input_data.is_idle_total,
            input_data.hour,
            input_data.day_of_week,
            input_data.is_weekend
        ]])
        
        # Scale features untuk CO2 emissions prediction
        features_scaled_emissions = scaler_co2_emissions.transform(features)
        pred_co2_emissions = model_co2_emissions.predict(features_scaled_emissions)[0]
        
        # Scale features untuk CO2 intensity prediction
        features_scaled_intensity = scaler_co2_intensity.transform(features)
        pred_co2_intensity = model_co2_intensity.predict(features_scaled_intensity)[0]
        
        # Ensure predictions are non-negative
        pred_co2_emissions = max(0, pred_co2_emissions)
        pred_co2_intensity = max(0, pred_co2_intensity)
        
        return EmissionPredictionOutput(
            co2_emissions_grams=round(pred_co2_emissions, 2),
            co2_intensity=round(pred_co2_intensity, 2),
            predictions={
                "co2_emissions_grams": round(pred_co2_emissions, 2),
                "co2_intensity": round(pred_co2_intensity, 2),
                "features_used": dict(zip(feature_cols, features[0].tolist()))
            }
        )
    
    except FileNotFoundError as e:
        raise Exception(f"Model loading error: {str(e)}")
    except Exception as e:
        raise Exception(f"Prediction error: {str(e)}")