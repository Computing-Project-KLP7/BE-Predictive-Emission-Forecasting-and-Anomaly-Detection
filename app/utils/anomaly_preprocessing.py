"""
Utility functions untuk preprocessing raw data untuk anomaly detection.
Digunakan untuk mempersiapkan data sebelum dikirim ke endpoint deteksi anomali.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from app.schemas.anomaly import AnomalyDetectionRequest, DailyAnomalyReportRequest


# CO2 emission factor
CO2_FACTOR = 2.68  # kg CO2 per liter diesel


def prepare_anomaly_detection_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Persiapan raw data untuk anomaly detection (per record).
    
    Args:
        df: DataFrame dengan kolom: timestamp, device_id, odometer_km,
            fuel_level_l, speed, rpm, ignition
            
    Returns:
        DataFrame dengan calculated features untuk anomaly detection
        
    Features yang dikalkulasi:
    - distance_delta: Jarak sejak record sebelumnya
    - fuel_delta: Perubahan fuel level
    - idle_duration: Durasi idle saat ini
    - engine_load: Beban mesin (%)
    - fuel_consumption_rate: Konsumsi per km
    - co2_intensity: Emisi per km
    """
    # Ensure datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Sort by device_id and timestamp
    df = df.sort_values(['device_id', 'timestamp']).reset_index(drop=True)
    
    # Calculate time delta in minutes
    df['time_delta'] = df.groupby('device_id')['timestamp'].diff().dt.total_seconds() / 60
    df['time_delta'] = df['time_delta'].fillna(0).clip(lower=0, upper=1440)
    
    # Calculate distance delta
    df['distance_delta'] = df.groupby('device_id')['odometer_km'].diff().fillna(0)
    df['distance_delta'] = df['distance_delta'].clip(lower=0, upper=200)
    
    # Calculate fuel delta (negative = consumption)
    df['fuel_delta'] = df.groupby('device_id')['fuel_level_l'].diff().fillna(0)
    df['fuel_delta'] = df['fuel_delta'].clip(lower=-50, upper=50)
    
    # Movement indicators
    df['is_idle'] = ((df['speed'] == 0) & (df['ignition'] == True)).astype(int)
    
    # Idle duration (in minutes)
    df['idle_duration'] = np.where(df['is_idle'] == 1, df['time_delta'], 0)
    df['idle_duration'] = df['idle_duration'].fillna(0)
    
    # Engine load as percentage
    max_rpm = df['rpm'].max()
    if max_rpm > 0:
        df['engine_load'] = (df['rpm'] / max_rpm) * 100
    else:
        df['engine_load'] = 0
    df['engine_load'] = df['engine_load'].fillna(0).clip(lower=0, upper=100)
    
    # Fuel consumption rate (L/km)
    df['fuel_consumption_rate'] = np.where(
        df['distance_delta'] > 0,
        (df['fuel_delta'] * -1) / df['distance_delta'],
        0  # Changed from np.nan to 0 for safer handling
    )
    df['fuel_consumption_rate'] = df['fuel_consumption_rate'].fillna(0).clip(lower=0, upper=2)
    
    # CO2 calculation
    df['co2_grams'] = (df['fuel_delta'] * -1).clip(lower=0) * CO2_FACTOR * 1000
    
    # CO2 intensity (g/km)
    df['co2_intensity'] = np.where(
        df['distance_delta'] > 0,
        df['co2_grams'] / df['distance_delta'],
        0  # Changed from np.nan to 0 for safer handling
    )
    df['co2_intensity'] = df['co2_intensity'].fillna(0).clip(lower=0, upper=1000)
    
    return df


def row_to_anomaly_detection_request(row: pd.Series) -> AnomalyDetectionRequest:
    """
    Konversi satu row dari prepared data menjadi AnomalyDetectionRequest.
    
    Args:
        row: Satu row dari hasil prepare_anomaly_detection_data
        
    Returns:
        AnomalyDetectionRequest siap untuk dikirim ke API
    """
    return AnomalyDetectionRequest(
        speed=float(row['speed']),
        distance_delta=float(row['distance_delta']),
        fuel_delta=float(row['fuel_delta']),
        fuel_consumption_rate=float(row['fuel_consumption_rate']),
        idle_duration=float(row['idle_duration']),
        rpm=float(row['rpm']),
        engine_load=float(row['engine_load']),
        co2_intensity=float(row['co2_intensity'])
    )


def prepare_daily_anomaly_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Agregasi data harian untuk deteksi excessive idle.
    
    Args:
        df: DataFrame yang sudah melalui prepare_anomaly_detection_data
        
    Returns:
        DataFrame dengan agregasi per hari
    """
    # Ensure timestamp is datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Extract date
    df['date'] = df['timestamp'].dt.date
    
    # Aggregate per day
    daily = df.groupby(['device_id', 'date']).agg({
        'idle_duration': 'sum',
        'co2_intensity': 'mean'
    }).reset_index()
    
    # Rename columns
    daily = daily.rename(columns={
        'idle_duration': 'total_idle_minutes',
        'co2_intensity': 'average_co2_intensity'
    })
    
    # Convert date to string format YYYY-MM-DD
    daily['date'] = daily['date'].astype(str)
    
    return daily


def row_to_daily_anomaly_request(row: pd.Series) -> DailyAnomalyReportRequest:
    """
    Konversi satu row dari daily aggregation menjadi DailyAnomalyReportRequest.
    
    Args:
        row: Satu row dari hasil prepare_daily_anomaly_data
        
    Returns:
        DailyAnomalyReportRequest siap untuk dikirim ke API
    """
    return DailyAnomalyReportRequest(
        device_id=int(row['device_id']),
        date=str(row['date']),
        total_idle_minutes=float(row['total_idle_minutes']),
        average_co2_intensity=float(row['average_co2_intensity'])
    )


def process_anomaly_detection_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Complete pipeline untuk mengubah raw data menjadi features siap anomaly detection.
    
    Args:
        df: Raw DataFrame dengan kolom: timestamp, device_id, odometer_km,
            fuel_level_l, speed, rpm, ignition
            
    Returns:
        DataFrame dengan calculated features siap untuk anomaly detection per record
        
    Example:
        >>> df_raw = pd.read_csv('raw_data.csv')
        >>> df_processed = process_anomaly_detection_pipeline(df_raw)
        >>> for idx, row in df_processed.iterrows():
        ...     request = row_to_anomaly_detection_request(row)
        ...     # Kirim request ke API
    """
    # Prepare data
    df_prepared = prepare_anomaly_detection_data(df.copy())
    
    return df_prepared


def get_statistics_for_emission_threshold(df: pd.DataFrame) -> dict:
    """
    Hitung statistik CO2 intensity dari data untuk threshold anomaly detection.
    
    Args:
        df: DataFrame dari hasil prepare_anomaly_detection_data
        
    Returns:
        Dictionary dengan mean dan std dari co2_intensity
        
    Note:
        Statistik ini digunakan untuk mendeteksi emission inefficiency.
        Threshold = mean + (2 * std)
    """
    # Filter valid values (tidak 0 atau NaN)
    valid_co2 = df[df['co2_intensity'] > 0]['co2_intensity']
    
    stats = {
        'co2_intensity_mean': float(valid_co2.mean()) if len(valid_co2) > 0 else 0,
        'co2_intensity_std': float(valid_co2.std()) if len(valid_co2) > 1 else 0,
        'co2_intensity_min': float(valid_co2.min()) if len(valid_co2) > 0 else 0,
        'co2_intensity_max': float(valid_co2.max()) if len(valid_co2) > 0 else 0,
        'sample_count': len(valid_co2)
    }
    
    return stats


# Example usage documentation
"""
# 1. Real-time anomaly detection (per record)
df = pd.read_csv('raw_data.csv')
df_processed = process_anomaly_detection_pipeline(df)

import requests
for idx, row in df_processed.iterrows():
    request = row_to_anomaly_detection_request(row)
    response = requests.post(
        "http://localhost:8000/api/v1/anomaly/detect",
        json=request.dict()
    )
    result = response.json()
    if result['is_anomaly']:
        print(f"⚠️ ANOMALY DETECTED: {result['anomaly_types']}")
        print(f"   Severity: {result['severity']}")

# 2. Daily anomaly report (aggregated)
df_daily = prepare_daily_anomaly_data(df_processed)

for idx, row in df_daily.iterrows():
    request = row_to_daily_anomaly_request(row)
    response = requests.post(
        "http://localhost:8000/api/v1/anomaly/daily-report",
        json=request.dict()
    )
    result = response.json()
    if result['excessive_idle_detected']:
        print(f"⚠️ EXCESSIVE IDLE DETECTED for {result['device_id']} on {result['date']}")
        print(f"   Total idle: {result['total_idle_minutes']:.0f} minutes ({result['idle_percentage']:.1f}%)")

# 3. Get statistics for threshold calibration
stats = get_statistics_for_emission_threshold(df_processed)
print(f"CO2 Intensity Stats: Mean={stats['co2_intensity_mean']:.2f}, "
      f"Std={stats['co2_intensity_std']:.2f}")
print(f"Threshold for inefficiency: {stats['co2_intensity_mean'] + 2*stats['co2_intensity_std']:.2f}")
"""
