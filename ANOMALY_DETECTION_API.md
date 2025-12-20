# 📊 Anomaly Detection API Documentation

## Endpoint Overview

Telah ditambahkan 2 endpoint untuk mendeteksi anomali pada data kendaraan:

### 1. POST `/api/v1/anomaly/detect`
Real-time anomaly detection per record dengan 4 jenis deteksi

### 2. POST `/api/v1/anomaly/daily-report`
Daily aggregation report untuk deteksi excessive idle

---

## Endpoint 1: Real-time Anomaly Detection

### POST `/api/v1/anomaly/detect`

Melakukan deteksi anomali real-time menggunakan 8 fitur raw data.

#### Request Body

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

#### Parameter Details

| Feature | Type | Deskripsi | Range | Contoh |
|---------|------|-----------|-------|--------|
| `speed` | float | Kecepatan saat ini | 0-200 km/h | 0 |
| `distance_delta` | float | Jarak sejak record sebelumnya | 0-200 km | 0 |
| `fuel_delta` | float | Perubahan fuel level (- = konsumsi) | -50 to +50 L | -10.0 |
| `fuel_consumption_rate` | float | Konsumsi per km | 0-2 L/km | 0 |
| `idle_duration` | float | Durasi idle record ini | 0-1440 menit | 5 |
| `rpm` | float | RPM mesin | 0-3000 | 0 |
| `engine_load` | float | Beban mesin | 0-100 % | 0 |
| `co2_intensity` | float | Emisi per km | 0-1000 g/km | 0 |

#### Response Format

```json
{
  "is_anomaly": true,
  "anomaly_score": -0.234,
  "anomaly_types": ["fuel_theft", "ml_detected"],
  "severity": "HIGH",
  "fuel_theft_detected": true,
  "excessive_idle_detected": false,
  "emission_inefficiency_detected": false,
  "ml_anomaly_detected": true,
  "fuel_theft_risk": 0.85,
  "emission_score": 0.15
}
```

#### Response Fields

| Field | Type | Deskripsi |
|-------|------|-----------|
| `is_anomaly` | boolean | Ada anomali terdeteksi atau tidak |
| `anomaly_score` | float | Score dari Isolation Forest (-1 to 1), lebih negatif = lebih anomali |
| `anomaly_types` | array | List jenis anomali: fuel_theft, emission_inefficiency, ml_detected |
| `severity` | enum | Level severity: LOW, MEDIUM, HIGH, CRITICAL |
| `fuel_theft_detected` | boolean | Apakah fuel theft terdeteksi |
| `excessive_idle_detected` | boolean | Apakah excessive idle terdeteksi (biasanya false di real-time) |
| `emission_inefficiency_detected` | boolean | Apakah emission inefficiency terdeteksi |
| `ml_anomaly_detected` | boolean | Apakah ML-based anomaly terdeteksi |
| `fuel_theft_risk` | float | Risk score untuk fuel theft (0-1) |
| `emission_score` | float | Emission intensity normalized score (0-1) |

---

## Endpoint 2: Daily Anomaly Report

### POST `/api/v1/anomaly/daily-report`

Laporan anomali harian dengan fokus pada excessive idle detection.

#### Request Body

```json
{
  "device_id": 101,
  "date": "2025-12-21",
  "total_idle_minutes": 180,
  "average_co2_intensity": 45.5
}
```

#### Parameter Details

| Field | Type | Deskripsi | Example |
|-------|------|-----------|---------|
| `device_id` | int | ID perangkat | 101 |
| `date` | string | Tanggal (YYYY-MM-DD) | "2025-12-21" |
| `total_idle_minutes` | float | Total idle dalam 1 hari (menit) | 180 |
| `average_co2_intensity` | float | Rata-rata CO2 intensity hari ini | 45.5 |

#### Response Format

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

#### Response Fields

| Field | Type | Deskripsi |
|-------|------|-----------|
| `device_id` | int | ID perangkat |
| `date` | string | Tanggal laporan |
| `excessive_idle_detected` | boolean | Apakah excessive idle terdeteksi |
| `total_idle_minutes` | float | Total idle dalam menit |
| `excessive_idle_threshold` | float | Threshold yang digunakan (default: 120 menit) |
| `idle_percentage` | float | Persentase idle time dari 24 jam (0-100) |
| `is_warning` | boolean | Warning jika > 80% dari threshold |

---

## 4 Jenis Anomali

### 1️⃣ Fuel Theft Detection (Rule-based)

**Kriteria:**
- Fuel drop > 5 liter (threshold)
- Kendaraan dalam keadaan diam (speed = 0)
- Tidak ada pergerakan (distance_delta < 0.1 km)

**Risk Score:** Dihitung dari magnitude fuel drop
- Semakin besar drop = semakin tinggi risk score

**Severity:** CRITICAL jika fuel_risk > 0.7

**Contoh:**
```
Speed: 0 km/h ✓
Distance: 0 km ✓
Fuel Drop: -10 liter ✓
→ FUEL THEFT DETECTED (risk: 0.85)
```

### 2️⃣ Excessive Idle Detection (Daily Aggregation)

**Kriteria:**
- Total idle minutes > 120 menit (2 jam) per hari

**Threshold:** Default 120 menit, dapat dikustomisasi

**Warning:** Muncul jika total idle > 80% dari threshold (> 96 menit)

**Note:** Deteksi ini memerlukan agregasi harian dan dilakukan di endpoint `/daily-report`

**Contoh:**
```
Total idle: 180 menit
Threshold: 120 menit
→ EXCESSIVE IDLE DETECTED
Percentage: 12.5% of 24 hours
```

### 3️⃣ Emission Inefficiency Detection (Statistical)

**Kriteria:**
- CO2 intensity > mean + (2 × std) dari historical data

**Thresholds:**
- Menggunakan 2-sigma rule (95% confidence)
- Threshold bersifat dinamis berdasarkan data historis
- Disimpan di `anomaly_detection_params.pkl`

**Score:** Normalized berdasarkan max CO2 intensity (1000 g/km)

**Contoh:**
```
Mean CO2 intensity: 40 g/km
Std Dev: 5 g/km
Threshold: 40 + (2 × 5) = 50 g/km
Current: 60 g/km
→ INEFFICIENCY DETECTED
```

### 4️⃣ ML-Based Anomaly (Isolation Forest)

**Model:** Isolation Forest dengan contamination rate 5%

**Features:** Menggunakan semua 8 fitur ML

**Score:** Continuous value -1 to 1
- Negatif = anomali
- Positif = normal

**Detection:**
- Anomaly jika model.predict() = -1
- Score < -0.5 = HIGH severity

**Advantage:** Mendeteksi anomali kombinasi yang kompleks

**Contoh:**
```
ML Score: -0.234
Prediction: -1 (ANOMALY)
→ ML ANOMALY DETECTED
```

---

## Severity Levels

| Level | Kondisi | Aksi |
|-------|---------|------|
| **CRITICAL** | Fuel theft detected (risk > 0.7) | ⛔ Immediate alert |
| **HIGH** | Multiple anomalies OR strong ML signal | 🔴 High priority |
| **MEDIUM** | Single anomaly terdeteksi | 🟡 Monitor |
| **LOW** | No anomaly but warning signs | 🟢 Info |

---

## Cara Membuat Features dari Raw Data

### Step 1: Sort Data
```python
df = df.sort_values(['device_id', 'timestamp']).reset_index(drop=True)
df['timestamp'] = pd.to_datetime(df['timestamp'])
```

### Step 2: Calculate Deltas
```python
# Time delta in minutes
df['time_delta'] = df.groupby('device_id')['timestamp'].diff().dt.total_seconds() / 60
df['time_delta'] = df['time_delta'].fillna(0).clip(lower=0, upper=1440)

# Distance delta
df['distance_delta'] = df.groupby('device_id')['odometer_km'].diff().fillna(0)
df['distance_delta'] = df['distance_delta'].clip(lower=0, upper=200)

# Fuel delta (negative = consumption)
df['fuel_delta'] = df.groupby('device_id')['fuel_level_l'].diff().fillna(0)
df['fuel_delta'] = df['fuel_delta'].clip(lower=-50, upper=50)
```

### Step 3: Calculate Idle Duration
```python
df['is_idle'] = ((df['speed'] == 0) & (df['ignition'] == True)).astype(int)
df['idle_duration'] = np.where(df['is_idle'] == 1, df['time_delta'], 0)
```

### Step 4: Calculate Engine Load
```python
max_rpm = df['rpm'].max()
df['engine_load'] = (df['rpm'] / max_rpm) * 100
df['engine_load'] = df['engine_load'].fillna(0).clip(lower=0, upper=100)
```

### Step 5: Calculate Fuel Consumption Rate
```python
df['fuel_consumption_rate'] = np.where(
    df['distance_delta'] > 0,
    (df['fuel_delta'] * -1) / df['distance_delta'],
    0
)
df['fuel_consumption_rate'] = df['fuel_consumption_rate'].clip(lower=0, upper=2)
```

### Step 6: Calculate CO2 Intensity
```python
CO2_FACTOR = 2.68  # kg CO2 per liter diesel
df['co2_grams'] = (df['fuel_delta'] * -1).clip(lower=0) * CO2_FACTOR * 1000
df['co2_intensity'] = np.where(
    df['distance_delta'] > 0,
    df['co2_grams'] / df['distance_delta'],
    0
)
df['co2_intensity'] = df['co2_intensity'].clip(lower=0, upper=1000)
```

---

## Python Example

### Real-time Anomaly Detection
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

print(f"Is Anomaly: {result['is_anomaly']}")
print(f"Severity: {result['severity']}")
print(f"Types: {result['anomaly_types']}")
print(f"Fuel Theft Risk: {result['fuel_theft_risk']:.2%}")
```

### From Raw Data
```python
import pandas as pd
from app.utils.anomaly_preprocessing import (
    process_anomaly_detection_pipeline,
    row_to_anomaly_detection_request
)
import requests

# Load and process data
df_raw = pd.read_csv('raw_data.csv')
df_processed = process_anomaly_detection_pipeline(df_raw)

# Real-time anomaly detection
for idx, row in df_processed.iterrows():
    request = row_to_anomaly_detection_request(row)
    
    response = requests.post(
        "http://localhost:8000/api/v1/anomaly/detect",
        json=request.dict()
    )
    
    result = response.json()
    if result['is_anomaly']:
        print(f"⚠️ Anomaly detected at {row['timestamp']}")
        print(f"   Types: {result['anomaly_types']}")
        print(f"   Severity: {result['severity']}")
```

### Daily Report
```python
import pandas as pd
from app.utils.anomaly_preprocessing import (
    prepare_anomaly_detection_data,
    prepare_daily_anomaly_data,
    row_to_daily_anomaly_request
)
import requests

# Process data
df_raw = pd.read_csv('raw_data.csv')
df_processed = prepare_anomaly_detection_data(df_raw)
df_daily = prepare_daily_anomaly_data(df_processed)

# Daily anomaly reports
for idx, row in df_daily.iterrows():
    request = row_to_daily_anomaly_request(row)
    
    response = requests.post(
        "http://localhost:8000/api/v1/anomaly/daily-report",
        json=request.dict()
    )
    
    result = response.json()
    if result['excessive_idle_detected']:
        print(f"⚠️ Excessive idle for device {result['device_id']} on {result['date']}")
        print(f"   Total idle: {result['total_idle_minutes']:.0f} min ({result['idle_percentage']:.1f}%)")
```

---

## Curl Examples

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

---

## Models & Parameters

**Lokasi:** `/app/models/`

| File | Deskripsi |
|------|-----------|
| `model_isolation_forest.pkl` | Isolation Forest model untuk ML-based anomaly detection |
| `scaler_anomaly_detection.pkl` | StandardScaler untuk normalisasi 8 features |
| `anomaly_detection_params.pkl` | Thresholds dan statistik (means, stds, dll) |
| `anomaly_detection_results.pkl` | Historical anomaly detection results (optional) |

**Caching:** Models, scalers, dan parameters di-cache di memory untuk performance optimal.

---

## Perbedaan dengan Emission Model

| Aspek | Emission Model | Anomaly Model |
|-------|---|---|
| **Granularity** | Per jam (hourly) | Per record (raw) |
| **Data Type** | Aggregated | Raw |
| **Features** | 12 (aggregated) | 8 (raw) |
| **Target** | Continuous (CO2 grams & intensity) | Binary (anomaly flags) |
| **Approach** | Regression | Classification + Rules |
| **Endpoint** | `/predict-hourly` | `/detect` & `/daily-report` |
| **Use Case** | Forecast emissions | Detect anomalies |

---

## Testing dengan FastAPI Docs

1. Jalankan server:
   ```bash
   python -m uvicorn app.main:app --reload
   ```

2. Buka browser:
   ```
   http://localhost:8000/docs
   ```

3. Cari endpoints:
   - `POST /api/v1/anomaly/detect`
   - `POST /api/v1/anomaly/daily-report`

4. Klik "Try it out" dan isikan request body

5. Klik "Execute" untuk menjalankan deteksi

---

## Error Handling

Jika ada error, API mengembalikan:

```json
{
  "detail": "Error message describing the issue"
}
```

**Common Errors:**
- **400 Bad Request** - Input tidak valid
- **422 Validation Error** - Format data tidak sesuai schema
- **500 Server Error** - Model file tidak ditemukan

Check `/logs/app.log` untuk detailed error information.

---

## Files Added/Modified

- ✨ [app/schemas/anomaly.py](app/schemas/anomaly.py) - NEW schema definitions
- ✨ [app/services/anomaly_service.py](app/services/anomaly_service.py) - NEW service logic
- ✏️ [app/api/v1/anomaly.py](app/api/v1/anomaly.py) - Updated endpoints
- ✨ [app/utils/anomaly_preprocessing.py](app/utils/anomaly_preprocessing.py) - NEW preprocessing utilities

