# 🚀 Quick Start Guide - Emission Prediction API

## Endpoint

```
POST /api/v1/emission/predict-hourly
```

## Minimal Request Example

```json
{
  "speed_mean": 45.5,
  "speed_max": 80.0,
  "speed_std": 15.2,
  "distance_delta_total": 50.0,
  "rpm_mean": 1500,
  "rpm_max": 2500,
  "engine_load_mean": 45.0,
  "is_moving_mean": 0.85,
  "is_idle_total": 9,
  "hour": 14,
  "day_of_week": 2,
  "is_weekend": 0
}
```

## Expected Response

```json
{
  "co2_grams_total": 2450.75,
  "co2_intensity_mean": 49.01,
  "unit_emissions": "grams/hour",
  "unit_intensity": "g/km"
}
```

## Quick Curl Test

```bash
curl -X POST "http://localhost:8000/api/v1/emission/predict-hourly" \
  -H "Content-Type: application/json" \
  -d '{
    "speed_mean": 45.5,
    "speed_max": 80.0,
    "speed_std": 15.2,
    "distance_delta_total": 50.0,
    "rpm_mean": 1500,
    "rpm_max": 2500,
    "engine_load_mean": 45.0,
    "is_moving_mean": 0.85,
    "is_idle_total": 9,
    "hour": 14,
    "day_of_week": 2,
    "is_weekend": 0
  }'
```

## 12 Required Features

| # | Feature | Type | Range | Example |
|---|---------|------|-------|---------|
| 1 | speed_mean | float | 0-200 km/h | 45.5 |
| 2 | speed_max | float | 0-200 km/h | 80.0 |
| 3 | speed_std | float | 0-100 | 15.2 |
| 4 | distance_delta_total | float | 0-200 km | 50.0 |
| 5 | rpm_mean | float | 0-3000 | 1500 |
| 6 | rpm_max | float | 0-3000 | 2500 |
| 7 | engine_load_mean | float | 0-100 % | 45.0 |
| 8 | is_moving_mean | float | 0-1 | 0.85 |
| 9 | is_idle_total | float | 0-60 menit | 9 |
| 10 | hour | int | 0-23 | 14 |
| 11 | day_of_week | int | 0-6 (0=Mon) | 2 |
| 12 | is_weekend | int | 0 atau 1 | 0 |

## Python Example

```python
import requests

url = "http://localhost:8000/api/v1/emission/predict-hourly"

payload = {
    "speed_mean": 45.5,
    "speed_max": 80.0,
    "speed_std": 15.2,
    "distance_delta_total": 50.0,
    "rpm_mean": 1500,
    "rpm_max": 2500,
    "engine_load_mean": 45.0,
    "is_moving_mean": 0.85,
    "is_idle_total": 9,
    "hour": 14,
    "day_of_week": 2,
    "is_weekend": 0
}

response = requests.post(url, json=payload)
result = response.json()

print(f"CO2 Emissions: {result['co2_grams_total']:.2f} grams/hour")
print(f"CO2 Intensity: {result['co2_intensity_mean']:.2f} g/km")
```

## From Raw Data (Complete Pipeline)

```python
import pandas as pd
from app.utils.emission_preprocessing import process_raw_data_pipeline, row_to_prediction_request
import requests

# Load raw data
df_raw = pd.read_csv('data.csv')

# Process to hourly features
df_hourly = process_raw_data_pipeline(df_raw)

# Make predictions
for idx, row in df_hourly.iterrows():
    request = row_to_prediction_request(row)
    
    response = requests.post(
        "http://localhost:8000/api/v1/emission/predict-hourly",
        json=request.dict()
    )
    
    result = response.json()
    print(f"Hour {row['date_hour']}: "
          f"{result['co2_grams_total']:.2f} g/h, "
          f"{result['co2_intensity_mean']:.2f} g/km")
```

## Raw Data Format Requirements

Your raw data must have these columns:
- `timestamp` (datetime)
- `device_id` (int)
- `odometer_km` (float)
- `fuel_level_l` (float)
- `speed` (float)
- `rpm` (int/float)
- `ignition` (bool)

## Test with FastAPI Docs

1. Run the server:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. Open your browser:
   ```
   http://localhost:8000/docs
   ```

3. Find endpoint: `POST /api/v1/emission/predict-hourly`

4. Click "Try it out" and paste the minimal request example

5. Click "Execute"

## Files Added/Modified

- ✏️ [app/schemas/emission.py](app/schemas/emission.py) - Added EmissionPredictionRequest & Response
- ✏️ [app/services/emission_service.py](app/services/emission_service.py) - Added predict_emission() function
- ✏️ [app/api/v1/emission.py](app/api/v1/emission.py) - Added /predict-hourly endpoint
- ✏️ [app/core/logging.py](app/core/logging.py) - Added logging setup
- ✨ [app/utils/emission_preprocessing.py](app/utils/emission_preprocessing.py) - NEW utility functions
- ✨ [EMISSION_PREDICTION_API.md](EMISSION_PREDICTION_API.md) - NEW full documentation
- ✨ [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - NEW detailed summary

## Models Used

Located in `/app/models/`:
- `model_co2_emissions.pkl` - Trained model for emissions prediction
- `model_co2_intensity.pkl` - Trained model for intensity prediction
- `scaler_co2_emissions.pkl` - StandardScaler for emissions features
- `scaler_co2_intensity.pkl` - StandardScaler for intensity features

## Response Interpretation

- **co2_grams_total**: Total CO2 emitted in grams during that hour
  - Higher = More pollution
  - Example: 2450.75 grams = ~2.45 kg CO2/hour

- **co2_intensity_mean**: CO2 per kilometer traveled
  - Higher = Less efficient
  - Example: 49.01 g/km means 49g CO2 per km driven

## Error Handling

If something goes wrong:

```json
{
  "detail": "Error message describing the issue"
}
```

Common issues:
- **400 Bad Request** - Invalid input format
- **422 Validation Error** - Missing or wrong data types
- **500 Server Error** - Model file not found or other server issue

Check `/logs/app.log` for detailed error information.

---

For more details, see [EMISSION_PREDICTION_API.md](EMISSION_PREDICTION_API.md) or [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)
