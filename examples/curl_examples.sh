#!/bin/bash

# Curl Commands untuk Testing Kedua Endpoint
# Base URL: http://localhost:8000 (local) atau https://your-domain.com (production)

echo "=== EMISSION PREDICTION ENDPOINT ==="

# Example 1: Normal driving
curl -X POST "http://localhost:8000/api/v1/emission/predict-hourly" \
  -H "Content-Type: application/json" \
  -d '{
    "speed_mean": 60.0,
    "speed_max": 90.0,
    "speed_std": 15.5,
    "distance_delta_total": 45.2,
    "rpm_mean": 1800.0,
    "rpm_max": 2200.0,
    "engine_load_mean": 50.0,
    "is_moving_mean": 0.85,
    "is_idle_total": 5,
    "hour": 14,
    "day_of_week": 3,
    "is_weekend": 0
  }'

echo -e "\n\n=== ANOMALY DETECTION - REAL-TIME ENDPOINT ==="

# Example 1: Fuel theft detected
curl -X POST "http://localhost:8000/api/v1/anomaly/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "speed": 0,
    "distance_delta": 0,
    "fuel_delta": -10.0,
    "fuel_consumption_rate": 0,
    "idle_duration": 5,
    "rpm": 0,
    "engine_load": 0,
    "co2_intensity": 0
  }'

# Example 2: Normal driving
curl -X POST "http://localhost:8000/api/v1/anomaly/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "speed": 60.0,
    "distance_delta": 1.2,
    "fuel_delta": -0.3,
    "fuel_consumption_rate": 0.25,
    "idle_duration": 0,
    "rpm": 1800,
    "engine_load": 50.0,
    "co2_intensity": 42.5
  }'

# Example 3: High emission
curl -X POST "http://localhost:8000/api/v1/anomaly/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "speed": 50.0,
    "distance_delta": 0.8,
    "fuel_delta": -0.6,
    "fuel_consumption_rate": 0.75,
    "idle_duration": 1,
    "rpm": 2000,
    "engine_load": 70.0,
    "co2_intensity": 150.0
  }'

echo -e "\n\n=== ANOMALY DETECTION - DAILY REPORT ENDPOINT ==="

# Example: Daily aggregation untuk excessive idle detection
curl -X POST "http://localhost:8000/api/v1/anomaly/daily-report" \
  -H "Content-Type: application/json" \
  -d '{
    "total_idle_minutes": 240,
    "total_distance_km": 125.5,
    "total_fuel_consumed_liters": 8.3,
    "average_co2_intensity": 55.2,
    "max_co2_intensity": 180.0,
    "total_harsh_accelerations": 3,
    "total_harsh_brakes": 2,
    "device_id": "VHCL001",
    "report_date": "2024-01-15"
  }'

echo -e "\n\nDone!"
