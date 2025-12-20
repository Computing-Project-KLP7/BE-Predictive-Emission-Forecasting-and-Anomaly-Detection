# 🚀 Anomaly Detection API - Quick Start

## Endpoints

```
POST /api/v1/anomaly/detect              (Real-time per record)
POST /api/v1/anomaly/daily-report        (Daily aggregation)
```

## Minimal Request Examples

### Real-time Detection
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

### Daily Report
```json
{
  "device_id": 101,
  "date": "2025-12-21",
  "total_idle_minutes": 180,
  "average_co2_intensity": 45.5
}
```

## Expected Responses

### Real-time Detection Response
```json
{
  "is_anomaly": true,
  "anomaly_score": -0.234,
  "anomaly_types": ["fuel_theft"],
  "severity": "CRITICAL",
  "fuel_theft_detected": true,
  "excessive_idle_detected": false,
  "emission_inefficiency_detected": false,
  "ml_anomaly_detected": false,
  "fuel_theft_risk": 0.85,
  "emission_score": 0.0
}
```

### Daily Report Response
```json
{
  "device_id": 101,
  "date": "2025-12-21",
  "excessive_idle_detected": true,
  "total_idle_minutes": 180.0,
  "excessive_idle_threshold": 120.0,
  "idle_percentage": 12.5,
  "is_warning": true
}
```

## Quick Curl Tests

### Real-time Detection
```bash
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
```

### Daily Report
```bash
curl -X POST "http://localhost:8000/api/v1/anomaly/daily-report" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 101,
    "date": "2025-12-21",
    "total_idle_minutes": 180,
    "average_co2_intensity": 45.5
  }'
```

## 8 Required Features

| # | Feature | Type | Range | Example |
|---|---------|------|-------|---------|
| 1 | speed | float | 0-200 km/h | 0 |
| 2 | distance_delta | float | 0-200 km | 0 |
| 3 | fuel_delta | float | -50 to +50 L | -10.0 |
| 4 | fuel_consumption_rate | float | 0-2 L/km | 0 |
| 5 | idle_duration | float | 0-1440 min | 5 |
| 6 | rpm | float | 0-3000 | 0 |
| 7 | engine_load | float | 0-100 % | 0 |
| 8 | co2_intensity | float | 0-1000 g/km | 0 |

## 4 Types of Anomalies Detected

1. **🚨 Fuel Theft** - Large fuel drop + stationary vehicle
   - Threshold: -5 liter
   - Severity: CRITICAL

2. **⏱️ Excessive Idle** - Too much idle time per day
   - Threshold: 120 minutes/day
   - Detection: Daily report endpoint

3. **💨 Emission Inefficiency** - Abnormally high CO2 intensity
   - Threshold: mean + 2×std (dynamic)
   - Detection: Statistical

4. **🤖 ML-Based Anomaly** - Isolation Forest
   - Features: All 8
   - Contamination: 5%

## Python Examples

### Real-time Detection
```python
import requests

url = "http://localhost:8000/api/v1/anomaly/detect"
payload = {
    "speed": 0,
    "distance_delta": 0,
    "fuel_delta": -10.0,
    "fuel_consumption_rate": 0,
    "idle_duration": 5,
    "rpm": 0,
    "engine_load": 0,
    "co2_intensity": 0
}

response = requests.post(url, json=payload)
result = response.json()

if result['is_anomaly']:
    print(f"⚠️ ANOMALY: {result['anomaly_types']}")
    print(f"Severity: {result['severity']}")
```

### From Raw Data (Complete Pipeline)
```python
import pandas as pd
from app.utils.anomaly_preprocessing import (
    process_anomaly_detection_pipeline,
    row_to_anomaly_detection_request
)
import requests

# Load and process
df_raw = pd.read_csv('data.csv')
df_processed = process_anomaly_detection_pipeline(df_raw)

# Detect anomalies
for idx, row in df_processed.iterrows():
    request = row_to_anomaly_detection_request(row)
    response = requests.post(
        "http://localhost:8000/api/v1/anomaly/detect",
        json=request.dict()
    )
    result = response.json()
    
    if result['is_anomaly']:
        print(f"🚨 {result['severity']}: {result['anomaly_types']}")
```

### Daily Aggregation Report
```python
import pandas as pd
from app.utils.anomaly_preprocessing import (
    process_anomaly_detection_pipeline,
    prepare_daily_anomaly_data,
    row_to_daily_anomaly_request
)
import requests

# Process data
df_raw = pd.read_csv('data.csv')
df_processed = process_anomaly_detection_pipeline(df_raw)
df_daily = prepare_daily_anomaly_data(df_processed)

# Daily reports
for idx, row in df_daily.iterrows():
    request = row_to_daily_anomaly_request(row)
    response = requests.post(
        "http://localhost:8000/api/v1/anomaly/daily-report",
        json=request.dict()
    )
    result = response.json()
    
    if result['excessive_idle_detected']:
        print(f"⏱️ Excessive idle: {result['total_idle_minutes']:.0f} min")
```

## Raw Data Format Requirements

Must have these columns:
- `timestamp` (datetime)
- `device_id` (int)
- `odometer_km` (float)
- `fuel_level_l` (float)
- `speed` (float)
- `rpm` (float)
- `ignition` (bool)

## Files Added/Modified

- ✨ [app/schemas/anomaly.py](app/schemas/anomaly.py) - Request/Response schemas
- ✨ [app/services/anomaly_service.py](app/services/anomaly_service.py) - Detection logic
- ✏️ [app/api/v1/anomaly.py](app/api/v1/anomaly.py) - Endpoints
- ✨ [app/utils/anomaly_preprocessing.py](app/utils/anomaly_preprocessing.py) - Data preprocessing

## Models Used

- `model_isolation_forest.pkl` - Isolation Forest for ML detection
- `scaler_anomaly_detection.pkl` - StandardScaler for 8 features
- `anomaly_detection_params.pkl` - Thresholds and statistics

## Test with FastAPI Docs

1. Run: `python -m uvicorn app.main:app --reload`
2. Open: `http://localhost:8000/docs`
3. Find: `POST /api/v1/anomaly/detect` or `POST /api/v1/anomaly/daily-report`
4. Click "Try it out"
5. Fill in request body
6. Click "Execute"

## Severity Levels

- 🟢 **LOW** - Warning signs only
- 🟡 **MEDIUM** - Single anomaly detected
- 🔴 **HIGH** - Multiple anomalies or strong ML signal
- ⛔ **CRITICAL** - Fuel theft detected

## Key Differences vs Emission Model

| Aspect | Anomaly | Emission |
|--------|---------|----------|
| Granularity | Per record | Per hour |
| Features | 8 (raw) | 12 (aggregated) |
| Target | Binary flags | Continuous values |
| Approach | Classification | Regression |

For full documentation, see [ANOMALY_DETECTION_API.md](ANOMALY_DETECTION_API.md)
