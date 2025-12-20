"""
Utility functions untuk preprocessing raw data menjadi hourly features.
Digunakan untuk mempersiapkan data sebelum dikirim ke endpoint prediksi.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from app.schemas.emission import EmissionPredictionRequest


# CO2 emission factor
CO2_FACTOR = 2.68  # kg CO2 per liter diesel


def calculate_co2_grams(fuel_consumed_liters: float) -> float:
    """
    Hitung emisi CO2 dalam gram dari konsumsi bahan bakar.
    
    Args:
        fuel_consumed_liters: Jumlah bahan bakar yang dikonsumsi dalam liter
        
    Returns:
        Emisi CO2 dalam gram
    """
    return fuel_consumed_liters * CO2_FACTOR * 1000


def prepare_raw_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Persiapan raw data sebelum agregasi.
    
    Args:
        df: DataFrame dengan kolom: timestamp, device_id, odometer_km, 
            fuel_level_l, speed, rpm, ignition
            
    Returns:
        DataFrame dengan delta values dan derived features
    """
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by device_id and timestamp
    df = df.sort_values(['device_id', 'timestamp']).reset_index(drop=True)
    
    # Calculate delta values
    df['distance_delta'] = df.groupby('device_id')['odometer_km'].diff().fillna(0)
    df['time_delta'] = df.groupby('device_id')['timestamp'].diff().dt.total_seconds().fillna(0) / 3600
    df['fuel_delta'] = (df.groupby('device_id')['fuel_level_l'].diff() * -1).fillna(0)
    
    # Calculate derived features
    df['is_moving'] = (df['speed'] > 0).astype(int)
    df['is_idle'] = ((df['speed'] == 0) & (df['ignition'] == True)).astype(int)
    
    # Engine load as percentage of max RPM
    max_rpm = df['rpm'].max()
    if max_rpm > 0:
        df['engine_load'] = (df['rpm'] / max_rpm) * 100
    else:
        df['engine_load'] = 0
    
    # Calculate CO2 emissions in grams
    df['co2_grams'] = df['fuel_delta'] * CO2_FACTOR * 1000
    
    # Extract hour and day of week
    df['hour'] = df['timestamp'].dt.hour
    df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['is_weekend'] = (df['day_of_week'].isin([5, 6])).astype(int)
    
    # Handle NaN values
    df = df.fillna(0)
    
    # Clean negative values that might result from sensor issues
    df.loc[df['distance_delta'] < 0, 'distance_delta'] = 0
    df.loc[df['fuel_delta'] < 0, 'fuel_delta'] = 0
    df.loc[df['co2_grams'] < 0, 'co2_grams'] = 0
    
    return df


def aggregate_to_hourly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agregasi raw data menjadi hourly features.
    
    Args:
        df: DataFrame yang sudah melalui prepare_raw_data
        
    Returns:
        DataFrame dengan fitur agregasi per jam
    """
    # Floor timestamp ke jam terdekat
    df['date_hour'] = df['timestamp'].dt.floor('H')
    
    # Aggregate
    hourly = df.groupby(['device_id', 'date_hour']).agg({
        'speed': ['mean', 'max', 'std'],
        'distance_delta': 'sum',
        'rpm': ['mean', 'max'],
        'engine_load': 'mean',
        'is_moving': 'mean',
        'is_idle': 'sum',
        'co2_grams': 'sum',
        'hour': 'first',
        'day_of_week': 'first',
        'is_weekend': 'first'
    }).reset_index()
    
    # Flatten multi-level columns
    hourly.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                       for col in hourly.columns.values]
    
    # Rename to match expected format
    hourly = hourly.rename(columns={
        'speed_mean': 'speed_mean',
        'speed_max': 'speed_max',
        'speed_std': 'speed_std',
        'distance_delta_sum': 'distance_delta_total',
        'rpm_mean': 'rpm_mean',
        'rpm_max': 'rpm_max',
        'engine_load_mean': 'engine_load_mean',
        'is_moving_mean': 'is_moving_mean',
        'is_idle_sum': 'is_idle_total',
        'hour_first': 'hour',
        'day_of_week_first': 'day_of_week',
        'is_weekend_first': 'is_weekend',
        'co2_grams_sum': 'co2_grams_total'
    })
    
    # Handle NaN from std calculation (when only 1 value)
    hourly = hourly.fillna(0)
    
    # Ensure data types
    hourly['hour'] = hourly['hour'].astype(int)
    hourly['day_of_week'] = hourly['day_of_week'].astype(int)
    hourly['is_weekend'] = hourly['is_weekend'].astype(int)
    
    return hourly


def row_to_prediction_request(row: pd.Series) -> EmissionPredictionRequest:
    """
    Konversi satu row dari hourly data menjadi EmissionPredictionRequest.
    
    Args:
        row: Satu row dari hasil aggregate_to_hourly
        
    Returns:
        EmissionPredictionRequest siap untuk dikirim ke API
    """
    return EmissionPredictionRequest(
        speed_mean=float(row['speed_mean']),
        speed_max=float(row['speed_max']),
        speed_std=float(row['speed_std']),
        distance_delta_total=float(row['distance_delta_total']),
        rpm_mean=float(row['rpm_mean']),
        rpm_max=float(row['rpm_max']),
        engine_load_mean=float(row['engine_load_mean']),
        is_moving_mean=float(row['is_moving_mean']),
        is_idle_total=float(row['is_idle_total']),
        hour=int(row['hour']),
        day_of_week=int(row['day_of_week']),
        is_weekend=int(row['is_weekend'])
    )


def process_raw_data_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Complete pipeline untuk mengubah raw data menjadi features siap prediksi.
    
    Args:
        df: Raw DataFrame dengan kolom: timestamp, device_id, odometer_km,
            fuel_level_l, speed, rpm, ignition
            
    Returns:
        DataFrame dengan hourly features siap untuk prediksi
        
    Example:
        >>> df_raw = pd.read_csv('raw_data.csv')
        >>> df_hourly = process_raw_data_pipeline(df_raw)
        >>> for idx, row in df_hourly.iterrows():
        ...     request = row_to_prediction_request(row)
        ...     # Kirim request ke API
    """
    # Step 1: Prepare raw data
    df_prepared = prepare_raw_data(df.copy())
    
    # Step 2: Aggregate to hourly
    df_hourly = aggregate_to_hourly(df_prepared)
    
    return df_hourly


# Example usage documentation
"""
# 1. Load raw data
df = pd.read_csv('data.csv')

# 2. Process menggunakan pipeline
df_hourly = process_raw_data_pipeline(df)

# 3. Create predictions
import requests

for idx, row in df_hourly.iterrows():
    request = row_to_prediction_request(row)
    
    response = requests.post(
        "http://localhost:8000/api/v1/emission/predict-hourly",
        json=request.dict()
    )
    
    result = response.json()
    print(f"Device {row['device_id']}, Hour {row['date_hour']}: "
          f"{result['co2_grams_total']:.2f} g/h, "
          f"{result['co2_intensity_mean']:.2f} g/km")
"""
