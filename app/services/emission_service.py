import joblib
import numpy as np
from pathlib import Path
from app.schemas.emission import EmissionPredictionRequest, EmissionPredictionResponse
from app.core.logging import logger


# Model and scaler paths
MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_CO2_EMISSIONS_PATH = MODEL_DIR / "model_co2_emissions.pkl"
MODEL_CO2_INTENSITY_PATH = MODEL_DIR / "model_co2_intensity.pkl"
SCALER_CO2_EMISSIONS_PATH = MODEL_DIR / "scaler_co2_emissions.pkl"
SCALER_CO2_INTENSITY_PATH = MODEL_DIR / "scaler_co2_intensity.pkl"

# Feature order (MUST match training order)
FEATURE_COLS = [
    'speed_mean',           # Rata-rata kecepatan dalam 1 jam
    'speed_max',            # Kecepatan maksimum dalam 1 jam
    'speed_std',            # Standar deviasi kecepatan dalam 1 jam
    'distance_delta_total', # Total jarak tempuh dalam 1 jam (km)
    'rpm_mean',             # Rata-rata RPM dalam 1 jam
    'rpm_max',              # RPM maksimum dalam 1 jam
    'engine_load_mean',     # Rata-rata engine load dalam 1 jam (%)
    'is_moving_mean',       # Proporsi waktu bergerak dalam 1 jam (0-1)
    'is_idle_total',        # Total durasi idle dalam 1 jam (menit)
    'hour',                 # Jam dalam sehari (0-23)
    'day_of_week',          # Hari dalam seminggu (0-6)
    'is_weekend'            # Apakah hari weekend (0/1)
]


class ModelLoader:
    """Loader untuk models dan scalers dengan caching"""
    _models_cache = {}
    _scalers_cache = {}
    
    @classmethod
    def load_model(cls, model_type: str):
        """Load model dengan caching"""
        if model_type == "co2_emissions":
            if "co2_emissions" not in cls._models_cache:
                cls._models_cache["co2_emissions"] = joblib.load(
                    MODEL_CO2_EMISSIONS_PATH
                )
            return cls._models_cache["co2_emissions"]
        elif model_type == "co2_intensity":
            if "co2_intensity" not in cls._models_cache:
                cls._models_cache["co2_intensity"] = joblib.load(
                    MODEL_CO2_INTENSITY_PATH
                )
            return cls._models_cache["co2_intensity"]
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    @classmethod
    def load_scaler(cls, scaler_type: str):
        """Load scaler dengan caching"""
        if scaler_type == "co2_emissions":
            if "co2_emissions" not in cls._scalers_cache:
                cls._scalers_cache["co2_emissions"] = joblib.load(
                    SCALER_CO2_EMISSIONS_PATH
                )
            return cls._scalers_cache["co2_emissions"]
        elif scaler_type == "co2_intensity":
            if "co2_intensity" not in cls._scalers_cache:
                cls._scalers_cache["co2_intensity"] = joblib.load(
                    SCALER_CO2_INTENSITY_PATH
                )
            return cls._scalers_cache["co2_intensity"]
        else:
            raise ValueError(f"Unknown scaler type: {scaler_type}")


def predict_emission(data: EmissionPredictionRequest) -> EmissionPredictionResponse:
    """
    Melakukan prediksi emisi CO2 berdasarkan fitur agregasi per jam.
    
    Args:
        data: EmissionPredictionRequest dengan 12 fitur
        
    Returns:
        EmissionPredictionResponse dengan prediksi CO2 emissions dan intensity
        
    Raises:
        Exception: Jika model atau scaler tidak dapat dimuat
    """
    try:
        logger.info("Starting emission prediction...")
        
        # Prepare features array
        features_dict = {
            'speed_mean': data.speed_mean,
            'speed_max': data.speed_max,
            'speed_std': data.speed_std,
            'distance_delta_total': data.distance_delta_total,
            'rpm_mean': data.rpm_mean,
            'rpm_max': data.rpm_max,
            'engine_load_mean': data.engine_load_mean,
            'is_moving_mean': data.is_moving_mean,
            'is_idle_total': data.is_idle_total,
            'hour': data.hour,
            'day_of_week': data.day_of_week,
            'is_weekend': data.is_weekend
        }
        
        # Create feature array in correct order
        features_array = np.array([[features_dict[col] for col in FEATURE_COLS]])
        logger.info(f"Features array shape: {features_array.shape}")
        logger.info(f"Features values: {features_array}")
        
        # Load models and scalers
        model_emissions = ModelLoader.load_model("co2_emissions")
        model_intensity = ModelLoader.load_model("co2_intensity")
        scaler_emissions = ModelLoader.load_scaler("co2_emissions")
        scaler_intensity = ModelLoader.load_scaler("co2_intensity")
        
        logger.info("Models and scalers loaded successfully")
        
        # Scale features for CO2 emissions prediction
        features_scaled_emissions = scaler_emissions.transform(features_array)
        logger.info(f"Scaled features for emissions: {features_scaled_emissions}")
        
        # Predict CO2 emissions (grams per hour)
        co2_emissions_pred = model_emissions.predict(features_scaled_emissions)
        co2_grams_total = float(co2_emissions_pred[0])
        
        logger.info(f"CO2 emissions prediction: {co2_grams_total} grams/hour")
        
        # Scale features for CO2 intensity prediction
        features_scaled_intensity = scaler_intensity.transform(features_array)
        logger.info(f"Scaled features for intensity: {features_scaled_intensity}")
        
        # Predict CO2 intensity (g/km)
        co2_intensity_pred = model_intensity.predict(features_scaled_intensity)
        co2_intensity_mean = float(co2_intensity_pred[0])
        
        logger.info(f"CO2 intensity prediction: {co2_intensity_mean} g/km")
        
        # Create response
        response = EmissionPredictionResponse(
            co2_grams_total=co2_grams_total,
            co2_intensity_mean=co2_intensity_mean
        )
        
        logger.info("Emission prediction completed successfully")
        return response
        
    except FileNotFoundError as e:
        logger.error(f"Model or scaler file not found: {e}")
        raise Exception(f"Model atau scaler tidak ditemukan: {str(e)}")
    except Exception as e:
        logger.error(f"Error during emission prediction: {e}")
        raise Exception(f"Error melakukan prediksi emisi: {str(e)}")