# 📋 Emission Prediction API Documentation

## Endpoint Overview

Telah ditambahkan endpoint baru untuk melakukan prediksi emisi CO2 berdasarkan fitur agregasi per jam:

### POST `/api/v1/emission/predict-hourly`

Endpoint ini menggunakan model machine learning yang telah dilatih untuk memprediksi:
1. **CO2 Emissions** - Total emisi CO2 dalam gram per jam
2. **CO2 Intensity** - Intensitas emisi dalam gram per kilometer

---

## Request Body

### Format Input

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

### Parameter Details

| Feature | Type | Deskripsi | Range | Contoh |
|---------|------|-----------|-------|--------|
| `speed_mean` | float | Rata-rata kecepatan dalam 1 jam | 0-200 km/h | 45.5 |
| `speed_max` | float | Kecepatan maksimum dalam 1 jam | 0-200 km/h | 80.0 |
| `speed_std` | float | Standar deviasi kecepatan | 0-100 | 15.2 |
| `distance_delta_total` | float | Total jarak tempuh dalam 1 jam | 0-200 km | 50.0 |
| `rpm_mean` | float | Rata-rata RPM mesin | 0-3000 | 1500 |
| `rpm_max` | float | RPM maksimum dalam 1 jam | 0-3000 | 2500 |
| `engine_load_mean` | float | Rata-rata engine load | 0-100 % | 45.0 |
| `is_moving_mean` | float | Proporsi waktu bergerak | 0-1 | 0.85 |
| `is_idle_total` | float | Total durasi idle | 0-60 menit | 9 |
| `hour` | int | Jam dalam sehari | 0-23 | 14 |
| `day_of_week` | int | Hari dalam seminggu (0=Senin) | 0-6 | 2 |
| `is_weekend` | int | Flag akhir pekan | 0 atau 1 | 0 |

---

## Response Format

```json
{
  "co2_grams_total": 2450.75,
  "co2_intensity_mean": 49.01,
  "unit_emissions": "grams/hour",
  "unit_intensity": "g/km"
}
```

### Response Fields

| Field | Type | Deskripsi |
|-------|------|-----------|
| `co2_grams_total` | float | Total prediksi emisi CO2 dalam gram per jam |
| `co2_intensity_mean` | float | Prediksi intensitas emisi dalam g/km |
| `unit_emissions` | string | Unit untuk total emisi (selalu "grams/hour") |
| `unit_intensity` | string | Unit untuk intensity (selalu "g/km") |

---

## Cara Membuat Features dari Raw Data

### 1. Hitung Delta Values (per record)

```python
# Hitung perubahan jarak dan waktu
df['distance_delta'] = df.groupby('device_id')['odometer_km'].diff()
df['time_delta'] = df.groupby('device_id')['timestamp'].diff().dt.total_seconds() / 3600
df['fuel_delta'] = df.groupby('device_id')['fuel_level_l'].diff() * -1
```

### 2. Hitung Derived Features

```python
# Tambahkan fitur turunan
df['is_moving'] = (df['speed'] > 0).astype(int)
df['is_idle'] = ((df['speed'] == 0) & (df['ignition'] == True)).astype(int)
df['engine_load'] = df['rpm'] / df['rpm'].max() * 100
```

### 3. Hitung CO2

```python
# Faktor emisi diesel: 2.68 kg CO2 per liter
CO2_FACTOR = 2.68  # kg CO2 per liter diesel
df['co2_grams'] = df['fuel_delta'] * CO2_FACTOR * 1000
```

### 4. Agregasi ke Hourly Data

```python
# Floor timestamp ke jam terdekat
df['date_hour'] = df['timestamp'].dt.floor('H')

# Agregasi per jam
hourly_data = df.groupby(['device_id', 'date_hour']).agg({
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

# Flatten column names
hourly_data.columns = ['_'.join(col).strip('_') if col[1] else col[0] 
                        for col in hourly_data.columns.values]

# Rename columns to match expected format
hourly_data = hourly_data.rename(columns={
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
    'is_weekend_first': 'is_weekend'
})
```

### 5. Gunakan Data untuk Prediksi

```python
import requests
import json

# Ambil satu row dari hourly_data
row = hourly_data.iloc[0]

# Siapkan payload
payload = {
    "speed_mean": float(row['speed_mean']),
    "speed_max": float(row['speed_max']),
    "speed_std": float(row['speed_std']),
    "distance_delta_total": float(row['distance_delta_total']),
    "rpm_mean": float(row['rpm_mean']),
    "rpm_max": float(row['rpm_max']),
    "engine_load_mean": float(row['engine_load_mean']),
    "is_moving_mean": float(row['is_moving_mean']),
    "is_idle_total": float(row['is_idle_total']),
    "hour": int(row['hour']),
    "day_of_week": int(row['day_of_week']),
    "is_weekend": int(row['is_weekend'])
}

# Make request
response = requests.post(
    "http://localhost:8000/api/v1/emission/predict-hourly",
    json=payload
)

# Get predictions
result = response.json()
print(f"CO2 Emissions: {result['co2_grams_total']} grams/hour")
print(f"CO2 Intensity: {result['co2_intensity_mean']} g/km")
```

---

## Error Handling

Jika terjadi error, API akan mengembalikan:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors:

1. **400 Bad Request** - Input tidak valid atau file model tidak ditemukan
2. **422 Unprocessable Entity** - Format data tidak sesuai dengan schema
3. **500 Internal Server Error** - Error internal saat melakukan prediksi

---

## Implementation Details

### Model Architecture

- **Model CO2 Emissions**: Memprediksi total emisi CO2 dalam gram per jam
- **Model CO2 Intensity**: Memprediksi intensitas emisi dalam g/km
- **Scaler**: StandardScaler untuk normalisasi features

### Feature Scaling

Semua features di-scale menggunakan StandardScaler sebelum diberikan ke model:

```python
from sklearn.preprocessing import StandardScaler

# Features di-scale per model
features_scaled = scaler.transform([[feature_values]])
prediction = model.predict(features_scaled)
```

### Model Loading

Models dan scalers di-load dari direktori `/app/models/`:

- `model_co2_emissions.pkl` - Model untuk prediksi emisi
- `model_co2_intensity.pkl` - Model untuk prediksi intensitas
- `scaler_co2_emissions.pkl` - Scaler untuk emisi
- `scaler_co2_intensity.pkl` - Scaler untuk intensity
- `emission_model_info.pkl` - Metadata model (optional)

Models di-cache di memori setelah first load untuk performance yang lebih baik.

---

## Curl Example

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

---

## Python Example

```python
import requests

url = "http://localhost:8000/api/v1/emission/predict-hourly"

data = {
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

response = requests.post(url, json=data)
result = response.json()

print(f"CO2 Emissions: {result['co2_grams_total']} grams/hour")
print(f"CO2 Intensity: {result['co2_intensity_mean']} g/km")
```

---

## Notes

⚠️ **Important Considerations:**

1. **Data Aggregation** - Features HARUS diagregasi per jam sebelum dikirim ke endpoint
2. **Feature Order** - Order features HARUS sesuai dengan order training
3. **Missing Values** - Jika ada missing values, gunakan `fillna(0)` atau median imputation
4. **Outliers** - Outliers harus di-clean sebelum agregasi
5. **Scaling** - Features akan di-scale otomatis oleh endpoint menggunakan StandardScaler yang sama dengan saat training

---

## File Changes

Berikut file yang telah diupdate:

1. **[app/schemas/emission.py](app/schemas/emission.py)** - Ditambahkan `EmissionPredictionRequest` dan `EmissionPredictionResponse`
2. **[app/services/emission_service.py](app/services/emission_service.py)** - Ditambahkan `predict_emission()` function dan `ModelLoader` class
3. **[app/api/v1/emission.py](app/api/v1/emission.py)** - Ditambahkan `/predict-hourly` endpoint
4. **[app/core/logging.py](app/core/logging.py)** - Setup logging untuk debugging

---

## Testing dengan FastAPI Docs

1. Jalankan server: `python -m uvicorn app.main:app --reload`
2. Buka browser: `http://localhost:8000/docs`
3. Cari endpoint `/api/v1/emission/predict-hourly`
4. Klik "Try it out" dan isikan request body dengan contoh data di atas
5. Klik "Execute" untuk menjalankan prediksi

