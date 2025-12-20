# 🏗️ Complete Backend Integration Guide

## Overview

Backend sekarang memiliki 2 model ML utama dengan masing-masing 1-2 endpoint:

### 1. **Emission Prediction Model** (Regression)
- Prediksi CO2 emissions per jam
- 12 aggregated features → 2 continuous predictions

### 2. **Anomaly Detection Model** (Classification + Rules)
- Deteksi anomali per record & daily report
- 8 raw features → 4 binary flags + severity

---

## 📊 Complete Architecture

```
Raw Vehicle Data
├── Odometer, Fuel level, Speed, RPM, Ignition, Timestamp
└── Per vehicle, timestamped
    ↓
    ├─────────────────────────────────────┐
    │                                     │
    ▼ (Raw data, per record)              ▼ (Aggregated, per hour)
    
ANOMALY DETECTION PIPELINE          EMISSION PREDICTION PIPELINE
├─ prepare_anomaly_detection_data() ├─ prepare_raw_data()
├─ Calculate 8 features:            ├─ Calculate deltas
│  • speed                           │  • distance_delta
│  • distance_delta                  │  • fuel_delta
│  • fuel_delta                      │  • rpm (mean, max)
│  • fuel_consumption_rate           │  • speed (mean, max, std)
│  • idle_duration                   │  • engine_load
│  • rpm                             │  • is_moving_mean
│  • engine_load                     │  • is_idle_total
│  • co2_intensity                   │  • co2_grams
│                                    │  • hour, day_of_week
├─ Real-time detection              ├─ aggregate_to_hourly()
│  /api/v1/anomaly/detect           │
│  └─ 4 anomaly types               ├─ Predict emissions
│     • Fuel theft                   │  /api/v1/emission/predict-hourly
│     • Emission inefficiency        │  └─ CO2 grams/hour + intensity
│     • ML-based (Isolation Forest)  │
│     • (Excessive idle per day)     └─ [Models]
│                                       • model_co2_emissions.pkl
├─ Daily aggregation                    • model_co2_intensity.pkl
│  /api/v1/anomaly/daily-report        • scaler_co2_emissions.pkl
│  └─ Excessive idle detection        • scaler_co2_intensity.pkl
│
└─ [Models]
   • model_isolation_forest.pkl
   • scaler_anomaly_detection.pkl
   • anomaly_detection_params.pkl
```

---

## 🔌 API Endpoints Summary

### Emission Prediction
```
POST /api/v1/emission/predict-hourly
├─ Input: 12 aggregated features (hourly)
├─ Output: CO2 grams/hour + CO2 intensity g/km
└─ Use case: Forecast vehicle emissions
```

### Anomaly Detection - Real-time
```
POST /api/v1/anomaly/detect
├─ Input: 8 raw features (per record)
├─ Output: 4 anomaly types + severity
└─ Use case: Detect suspicious behavior real-time
```

### Anomaly Detection - Daily Report
```
POST /api/v1/anomaly/daily-report
├─ Input: Daily aggregation (idle time)
├─ Output: Excessive idle detection
└─ Use case: Daily monitoring of vehicle idle time
```

---

## 📝 Workflow Examples

### Scenario 1: Real-time Anomaly Monitoring

```
Vehicle Event Every N Seconds
    ↓
Raw Data Record
    ├─ timestamp, device_id, speed, fuel_level, rpm, ignition, odometer
    ↓
prepare_anomaly_detection_data()
    ├─ Calculate deltas (distance, fuel, time)
    ├─ Calculate derived features (idle, engine_load, CO2)
    └─ Generate 8 features
    ↓
row_to_anomaly_detection_request()
    └─ Convert to request format
    ↓
POST /api/v1/anomaly/detect
    ↓
Response
    ├─ is_anomaly: true/false
    ├─ anomaly_types: [list]
    ├─ severity: LOW|MEDIUM|HIGH|CRITICAL
    └─ Individual flags
    ↓
Alert System
    ├─ If CRITICAL: Immediate alert
    ├─ If HIGH: Log + notify
    ├─ If MEDIUM: Monitor
    └─ If LOW: Info only
```

### Scenario 2: Hourly Emission Forecast

```
Raw Data Collected Over 1 Hour
    ├─ Multiple records per vehicle per hour
    ↓
prepare_raw_data()
    ├─ Calculate deltas
    ├─ Calculate derived features
    └─ Generate raw features
    ↓
aggregate_to_hourly()
    ├─ Group by device_id, date_hour
    ├─ Aggregate: speed (mean, max, std)
    ├─ Aggregate: rpm (mean, max)
    ├─ Aggregate: fuel consumption
    ├─ Aggregate: idle time
    └─ Generate 12 features
    ↓
row_to_prediction_request()
    └─ Convert to request format
    ↓
POST /api/v1/emission/predict-hourly
    ↓
Response
    ├─ co2_grams_total: XX grams/hour
    └─ co2_intensity_mean: XX g/km
    ↓
Dashboard
    ├─ Store predictions
    ├─ Visualize trends
    ├─ Compare with targets
    └─ Generate reports
```

### Scenario 3: Daily Idle Time Monitoring

```
Daily Data (All Records for Device for 1 Day)
    ↓
prepare_anomaly_detection_data()
    ├─ Calculate idle_duration for each record
    ↓
prepare_daily_anomaly_data()
    ├─ Group by device_id, date
    ├─ Sum total idle_duration
    ├─ Calculate average CO2 intensity
    └─ Generate daily aggregation
    ↓
row_to_daily_anomaly_request()
    └─ Convert to request format
    ↓
POST /api/v1/anomaly/daily-report
    ↓
Response
    ├─ excessive_idle_detected: true/false
    ├─ total_idle_minutes: XX
    ├─ idle_percentage: X% of 24 hours
    └─ is_warning: true/false
    ↓
Report System
    ├─ If excessive_idle: Flag for fleet manager
    ├─ If warning (80%): Send notification
    └─ Store in history
```

---

## 🔄 Data Flow for Complete Pipeline

### Input Data Requirements

**Raw Data Table:**
```
timestamp          device_id  odometer_km  fuel_level_l  speed  rpm  ignition
2025-12-21 10:00  101        1500.5       45.2          0      0    true
2025-12-21 10:01  101        1500.5       45.2          45     1500 true
2025-12-21 10:02  101        1501.2       44.8          60     1800 true
...
```

### Processing Steps

#### For Anomaly Detection:
1. Raw data → prepare_anomaly_detection_data() → 8 features per record
2. Per-record detection → POST /anomaly/detect
3. Daily aggregation → prepare_daily_anomaly_data() → Daily report → POST /anomaly/daily-report

#### For Emission Prediction:
1. Raw data → prepare_raw_data() → Raw features
2. Group by hour → aggregate_to_hourly() → 12 features per hour
3. Prediction → POST /emission/predict-hourly

---

## 🛠️ Integration Steps

### Step 1: Prepare Raw Data

```python
import pandas as pd
from app.utils.anomaly_preprocessing import process_anomaly_detection_pipeline
from app.utils.emission_preprocessing import process_raw_data_pipeline

# Load your data
df_raw = pd.read_csv('vehicle_data.csv')

# Prepare for anomaly detection (per record)
df_anomaly = process_anomaly_detection_pipeline(df_raw)

# Prepare for emission prediction (per hour)
df_emission = process_raw_data_pipeline(df_raw)
```

### Step 2: Send Real-time Anomaly Detection

```python
from app.utils.anomaly_preprocessing import row_to_anomaly_detection_request
import requests

for idx, row in df_anomaly.iterrows():
    request = row_to_anomaly_detection_request(row)
    response = requests.post(
        "http://localhost:8000/api/v1/anomaly/detect",
        json=request.dict()
    )
    
    result = response.json()
    if result['is_anomaly']:
        print(f"Alert: {result['severity']} - {result['anomaly_types']}")
```

### Step 3: Send Hourly Emission Prediction

```python
from app.utils.emission_preprocessing import row_to_prediction_request
import requests

for idx, row in df_emission.iterrows():
    request = row_to_prediction_request(row)
    response = requests.post(
        "http://localhost:8000/api/v1/emission/predict-hourly",
        json=request.dict()
    )
    
    result = response.json()
    print(f"Emissions: {result['co2_grams_total']:.0f} g/h, "
          f"Intensity: {result['co2_intensity_mean']:.2f} g/km")
```

### Step 4: Send Daily Idle Report

```python
from app.utils.anomaly_preprocessing import (
    prepare_daily_anomaly_data,
    row_to_daily_anomaly_request
)
import requests

df_daily = prepare_daily_anomaly_data(df_anomaly)

for idx, row in df_daily.iterrows():
    request = row_to_daily_anomaly_request(row)
    response = requests.post(
        "http://localhost:8000/api/v1/anomaly/daily-report",
        json=request.dict()
    )
    
    result = response.json()
    if result['excessive_idle_detected']:
        print(f"⚠️ Device {result['device_id']}: {result['idle_percentage']:.1f}% idle")
```

---

## 📊 Feature Comparison

### Anomaly Detection Features (8)
```
1. speed              - Current speed (0-200 km/h)
2. distance_delta     - Distance since last record (0-200 km)
3. fuel_delta         - Fuel change (-50 to +50 L)
4. fuel_consumption   - Consumption per km (0-2 L/km)
5. idle_duration      - Idle time (0-1440 min)
6. rpm                - Engine speed (0-3000)
7. engine_load        - Engine load (0-100%)
8. co2_intensity      - CO2 per km (0-1000 g/km)
```

### Emission Prediction Features (12)
```
1. speed_mean         - Average speed (km/h)
2. speed_max          - Max speed (km/h)
3. speed_std          - Speed variation
4. distance_delta     - Total distance (km)
5. rpm_mean           - Average RPM
6. rpm_max            - Max RPM
7. engine_load_mean   - Average load (%)
8. is_moving_mean     - Proportion moving (0-1)
9. is_idle_total      - Total idle (min)
10. hour              - Hour of day (0-23)
11. day_of_week       - Day (0-6, 0=Mon)
12. is_weekend        - Weekend flag (0/1)
```

---

## 🔒 Model Files Required

Place these in `/app/models/`:

### Emission Models
- `model_co2_emissions.pkl` - Regressor for emissions
- `model_co2_intensity.pkl` - Regressor for intensity
- `scaler_co2_emissions.pkl` - Scaler for emissions
- `scaler_co2_intensity.pkl` - Scaler for intensity
- `emission_model_info.pkl` - Metadata (optional)

### Anomaly Models
- `model_isolation_forest.pkl` - Isolation Forest classifier
- `scaler_anomaly_detection.pkl` - Scaler for anomaly features
- `anomaly_detection_params.pkl` - Thresholds & statistics
- `anomaly_detection_results.pkl` - Historical results (optional)

---

## 🚀 Quick Start Commands

### 1. Start Server
```bash
python -m uvicorn app.main:app --reload
```

### 2. Test Anomaly Detection
```bash
curl -X POST "http://localhost:8000/api/v1/anomaly/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "speed": 0, "distance_delta": 0, "fuel_delta": -10.0,
    "fuel_consumption_rate": 0, "idle_duration": 5,
    "rpm": 0, "engine_load": 0, "co2_intensity": 0
  }'
```

### 3. Test Emission Prediction
```bash
curl -X POST "http://localhost:8000/api/v1/emission/predict-hourly" \
  -H "Content-Type: application/json" \
  -d '{
    "speed_mean": 45.5, "speed_max": 80.0, "speed_std": 15.2,
    "distance_delta_total": 50.0, "rpm_mean": 1500, "rpm_max": 2500,
    "engine_load_mean": 45.0, "is_moving_mean": 0.85,
    "is_idle_total": 9, "hour": 14, "day_of_week": 2, "is_weekend": 0
  }'
```

### 4. Test Daily Report
```bash
curl -X POST "http://localhost:8000/api/v1/anomaly/daily-report" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 101, "date": "2025-12-21",
    "total_idle_minutes": 180, "average_co2_intensity": 45.5
  }'
```

### 5. Test with FastAPI Docs
```
http://localhost:8000/docs
```

---

## 📚 Documentation References

- **Emission Prediction:**
  - [EMISSION_PREDICTION_API.md](EMISSION_PREDICTION_API.md)
  - [QUICK_START.md](QUICK_START.md)
  - [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

- **Anomaly Detection:**
  - [ANOMALY_DETECTION_API.md](ANOMALY_DETECTION_API.md)
  - [ANOMALY_QUICK_START.md](ANOMALY_QUICK_START.md)
  - [ANOMALY_IMPLEMENTATION_SUMMARY.md](ANOMALY_IMPLEMENTATION_SUMMARY.md)

- **Code:**
  - [app/schemas/emission.py](app/schemas/emission.py)
  - [app/schemas/anomaly.py](app/schemas/anomaly.py)
  - [app/services/emission_service.py](app/services/emission_service.py)
  - [app/services/anomaly_service.py](app/services/anomaly_service.py)
  - [app/api/v1/emission.py](app/api/v1/emission.py)
  - [app/api/v1/anomaly.py](app/api/v1/anomaly.py)
  - [app/utils/emission_preprocessing.py](app/utils/emission_preprocessing.py)
  - [app/utils/anomaly_preprocessing.py](app/utils/anomaly_preprocessing.py)

---

## ✅ Verification Checklist

- [x] All syntax validated (no Python errors)
- [x] All imports correct
- [x] All models referenced correctly
- [x] All feature orders match training
- [x] Error handling implemented
- [x] Logging configured
- [x] Preprocessing utilities complete
- [x] Documentation comprehensive
- [x] Examples provided
- [x] Ready for production

---

**Status:** ✅ **PRODUCTION READY**

All endpoints tested and validated. Both models integrated successfully.

