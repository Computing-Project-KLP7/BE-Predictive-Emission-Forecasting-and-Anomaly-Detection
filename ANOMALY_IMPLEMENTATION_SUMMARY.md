# 🎯 Anomaly Detection Implementation Summary

## ✅ Status: SELESAI

Telah berhasil menambahkan 2 endpoint untuk deteksi anomali real-time menggunakan machine learning dan rule-based detection.

---

## 📁 File yang Telah Dibuat/Dimodifikasi

### 1. **[app/schemas/anomaly.py](app/schemas/anomaly.py)** ✨ BARU

**Schemas dibuat:**

```python
class AnomalyDetectionRequest(BaseModel):
    # 8 features untuk real-time detection per record
    speed, distance_delta, fuel_delta, fuel_consumption_rate,
    idle_duration, rpm, engine_load, co2_intensity

class AnomalyDetectionResponse(BaseModel):
    # Response dengan 4 jenis anomali detection
    is_anomaly, anomaly_score, anomaly_types, severity,
    fuel_theft_detected, excessive_idle_detected,
    emission_inefficiency_detected, ml_anomaly_detected,
    fuel_theft_risk, emission_score

class DailyAnomalyReportRequest(BaseModel):
    # Request untuk daily aggregation report
    device_id, date, total_idle_minutes, average_co2_intensity

class DailyAnomalyReportResponse(BaseModel):
    # Response untuk excessive idle detection per hari
    excessive_idle_detected, idle_percentage, is_warning, ...

class SeverityLevel(Enum):
    # LOW, MEDIUM, HIGH, CRITICAL
```

### 2. **[app/services/anomaly_service.py](app/services/anomaly_service.py)** ✨ BARU

**Functions & Classes:**

```python
class AnomalyModelLoader:
    # Load models, scalers, params dengan caching
    load_model()          # Isolation Forest
    load_scaler()         # StandardScaler
    load_params()         # Thresholds & statistics

def detect_fuel_theft():
    # Rule-based: Fuel drop > -5L + speed=0 + distance<0.1
    # Returns: is_theft, risk_score

def detect_emission_inefficiency():
    # Statistical: CO2 > mean + 2*std
    # Returns: is_inefficient

def calculate_severity():
    # Determine severity based on anomaly count & scores
    # Returns: SeverityLevel

def detect_anomaly():
    # Main function for real-time detection
    # Combines: Fuel theft + Emission inefficiency + ML-based
    # Returns: AnomalyDetectionResponse

def detect_daily_anomaly():
    # Daily aggregation for excessive idle
    # Returns: DailyAnomalyReportResponse
```

### 3. **[app/api/v1/anomaly.py](app/api/v1/anomaly.py)** ✏️ DIMODIFIKASI

**Endpoints ditambahkan:**

```python
@router.post("/detect", response_model=AnomalyDetectionResponse)
def detect(data: AnomalyDetectionRequest):
    """Real-time anomaly detection per record"""
    
@router.post("/daily-report", response_model=DailyAnomalyReportResponse)
def daily_anomaly_report(data: DailyAnomalyReportRequest):
    """Daily aggregation for excessive idle detection"""
```

### 4. **[app/utils/anomaly_preprocessing.py](app/utils/anomaly_preprocessing.py)** ✨ BARU

**Utility functions:**

```python
def prepare_anomaly_detection_data():
    # Calculate all 8 features dari raw data

def row_to_anomaly_detection_request():
    # Convert row to request format

def prepare_daily_anomaly_data():
    # Aggregate data per hari

def row_to_daily_anomaly_request():
    # Convert daily row to request format

def process_anomaly_detection_pipeline():
    # Complete pipeline: raw → features

def get_statistics_for_emission_threshold():
    # Calculate mean & std for threshold calibration
```

### 5. **[ANOMALY_DETECTION_API.md](ANOMALY_DETECTION_API.md)** ✨ BARU

Dokumentasi lengkap dengan:
- Endpoint overview
- Request/response format detail
- Feature descriptions
- 4 jenis anomali detection
- Severity levels
- Feature calculation dari raw data
- Python & curl examples
- Models & parameters info

### 6. **[ANOMALY_QUICK_START.md](ANOMALY_QUICK_START.md)** ✨ BARU

Quick reference dengan:
- Minimal examples
- Quick curl tests
- Python code snippets
- Models info
- Key differences vs Emission model

---

## 🎯 2 Endpoints Baru

### 1. Real-time Anomaly Detection
```
POST /api/v1/anomaly/detect
```

**Input:** 8 features per record
**Output:** 4 jenis anomali detection + severity

### 2. Daily Anomaly Report
```
POST /api/v1/anomaly/daily-report
```

**Input:** Daily aggregation (device, date, idle time)
**Output:** Excessive idle detection + warning

---

## 🚨 4 Jenis Anomali yang Terdeteksi

### 1️⃣ Fuel Theft (Rule-based)
- **Kriteria:** Fuel drop > -5L + speed=0 + distance<0.1km
- **Risk Score:** 0-1 (magnitude of drop)
- **Severity:** CRITICAL jika risk > 0.7

### 2️⃣ Excessive Idle (Daily aggregation)
- **Kriteria:** Total idle > 120 menit per hari
- **Warning:** Muncul di 80% threshold (96 menit)
- **Endpoint:** `/daily-report`

### 3️⃣ Emission Inefficiency (Statistical)
- **Kriteria:** CO2 intensity > mean + 2×std
- **Threshold:** Dynamic berdasarkan historical data
- **Detection:** Per record

### 4️⃣ ML-Based Anomaly (Isolation Forest)
- **Model:** Isolation Forest (contamination: 5%)
- **Features:** Semua 8 features
- **Score:** -1 to 1 (negatif = anomali)

---

## 📊 Features Diagram

```
Raw Data (per record)
    ↓
prepare_anomaly_detection_data()
    ├─ Calculate distance_delta
    ├─ Calculate fuel_delta
    ├─ Calculate idle_duration
    ├─ Calculate engine_load
    ├─ Calculate fuel_consumption_rate
    ├─ Calculate co2_grams & co2_intensity
    └─ Handle NaN & outliers
    ↓
8 ML Features
    ├─ speed
    ├─ distance_delta
    ├─ fuel_delta
    ├─ fuel_consumption_rate
    ├─ idle_duration
    ├─ rpm
    ├─ engine_load
    └─ co2_intensity
    ↓
AnomalyDetectionRequest
    ↓
detect_anomaly()
    ├─ Load Isolation Forest model
    ├─ Load StandardScaler
    ├─ Load thresholds & params
    ├─ Scale features
    ├─ Detect fuel theft (rule)
    ├─ Detect emission inefficiency (statistical)
    ├─ Detect ML anomaly
    ├─ Calculate severity
    └─ Return response
    ↓
AnomalyDetectionResponse
    ├─ is_anomaly
    ├─ anomaly_score
    ├─ anomaly_types
    ├─ severity
    ├─ Individual flags
    └─ Risk scores
```

---

## ⚙️ Detection Workflow

### Real-time Detection (/detect)
```
Request (8 features per record)
    ↓
Load models & params (cached)
    ↓
1. Fuel Theft Detection
   ├─ Check: fuel_delta < -5 & speed=0 & distance<0.1
   └─ Risk: magnitude of drop
    ↓
2. Emission Inefficiency
   ├─ Load: mean & std dari params
   └─ Check: co2_intensity > mean + 2*std
    ↓
3. ML-based Detection
   ├─ Scale features
   ├─ Isolation Forest predict
   └─ Score + flag
    ↓
4. Calculate Severity
   ├─ CRITICAL: fuel_theft & risk>0.7
   ├─ HIGH: multiple anomalies
   ├─ MEDIUM: single anomaly
   └─ LOW: no anomaly
    ↓
Response (4 flags + severity + scores)
```

### Daily Report (/daily-report)
```
Request (aggregated per day)
    ↓
Load params
    ↓
Calculate excessive idle
    ├─ Check: total_idle > 120 min
    └─ Warning: total_idle > 96 min
    ↓
Calculate idle percentage
    ├─ idle_minutes / 1440 * 100
    └─ Show % of 24 hours
    ↓
Response (excessive_idle_detected + percentage + warning)
```

---

## 🔐 Models & Parameters

**Lokasi:** `/app/models/`

| File | Deskripsi | Size |
|------|-----------|------|
| `model_isolation_forest.pkl` | Isolation Forest untuk ML detection | - |
| `scaler_anomaly_detection.pkl` | StandardScaler untuk 8 features | - |
| `anomaly_detection_params.pkl` | Thresholds & statistics | - |
| `anomaly_detection_results.pkl` | Historical results (optional) | - |

**Caching:** Models, scalers, dan params di-cache di memory setelah first load.

---

## 📋 Severity Levels

| Level | Kondisi | Aksi |
|-------|---------|------|
| **CRITICAL** | Fuel theft detected (risk > 0.7) | ⛔ Immediate alert |
| **HIGH** | Multiple anomalies OR ML score < -0.5 | 🔴 High priority |
| **MEDIUM** | Single anomaly terdeteksi | 🟡 Monitor |
| **LOW** | No anomaly but warning signs | 🟢 Info |

---

## 🧪 Testing Examples

### Real-time Detection Test
```bash
curl -X POST "http://localhost:8000/api/v1/anomaly/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "speed": 0, "distance_delta": 0, "fuel_delta": -10.0,
    "fuel_consumption_rate": 0, "idle_duration": 5,
    "rpm": 0, "engine_load": 0, "co2_intensity": 0
  }'
```

### Daily Report Test
```bash
curl -X POST "http://localhost:8000/api/v1/anomaly/daily-report" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": 101, "date": "2025-12-21",
    "total_idle_minutes": 180, "average_co2_intensity": 45.5
  }'
```

### From Raw Data (Python)
```python
import pandas as pd
from app.utils.anomaly_preprocessing import (
    process_anomaly_detection_pipeline,
    row_to_anomaly_detection_request
)
import requests

df_raw = pd.read_csv('data.csv')
df_processed = process_anomaly_detection_pipeline(df_raw)

for idx, row in df_processed.iterrows():
    request = row_to_anomaly_detection_request(row)
    response = requests.post(
        "http://localhost:8000/api/v1/anomaly/detect",
        json=request.dict()
    )
    result = response.json()
    if result['is_anomaly']:
        print(f"⚠️ {result['severity']}: {result['anomaly_types']}")
```

---

## ✅ Checklist Implementation

- [x] Schema untuk real-time detection (8 features)
- [x] Schema untuk daily report (idle aggregation)
- [x] Schema untuk response (4 flags + severity)
- [x] Rule-based fuel theft detection
- [x] Statistical emission inefficiency detection
- [x] ML-based Isolation Forest detection
- [x] Daily excessive idle detection
- [x] Severity calculation logic
- [x] Service dengan caching models
- [x] Endpoint `/detect` untuk real-time
- [x] Endpoint `/daily-report` untuk daily
- [x] Error handling & validation
- [x] Logging setup
- [x] Preprocessing utilities (prepare + row conversion)
- [x] Daily aggregation utilities
- [x] Documentation (API docs)
- [x] Quick start guide
- [x] Syntax validation (all files passing)

---

## 📚 Documentation Files

- [ANOMALY_DETECTION_API.md](ANOMALY_DETECTION_API.md) - Lengkap API documentation
- [ANOMALY_QUICK_START.md](ANOMALY_QUICK_START.md) - Quick reference guide
- [app/schemas/anomaly.py](app/schemas/anomaly.py) - Schema definitions
- [app/services/anomaly_service.py](app/services/anomaly_service.py) - Service logic
- [app/api/v1/anomaly.py](app/api/v1/anomaly.py) - Endpoint definitions
- [app/utils/anomaly_preprocessing.py](app/utils/anomaly_preprocessing.py) - Preprocessing utilities

---

## 🔄 Perbedaan dengan Emission Model

| Aspek | Anomaly Model | Emission Model |
|-------|---|---|
| **Granularity** | Per record (raw) | Per jam (hourly) |
| **Data Type** | Raw values | Aggregated values |
| **Features** | 8 (raw) | 12 (aggregated) |
| **Target** | Binary flags + continuous scores | Continuous values |
| **Approach** | Classification + Rules | Regression |
| **Endpoints** | `/detect` + `/daily-report` | `/predict-hourly` |
| **Use Case** | Detect anomalies | Forecast emissions |
| **Aggregation** | Per hari (untuk excessive idle) | Per jam |

---

## 🎓 Next Steps (Optional)

1. **Add batch anomaly detection** - `/detect-batch` untuk multiple records
2. **Add anomaly history** - Store detected anomalies di database
3. **Add real-time streaming** - Kafka/WebSocket untuk live detection
4. **Add anomaly rules management** - Endpoint untuk customize thresholds
5. **Add performance metrics** - Track detection accuracy
6. **Add alerts integration** - Email/SMS notifications
7. **Add pattern analysis** - Detect recurring anomalies
8. **Add ML model retraining** - Update Isolation Forest periodically

---

## 📞 Support

Untuk debugging:

1. Check [ANOMALY_DETECTION_API.md](ANOMALY_DETECTION_API.md) untuk API details
2. Check `/logs/app.log` untuk error information
3. Verify models exist di `/app/models/`
4. Verify data format matches schema

---

**Created:** 2025-12-21
**Status:** ✅ Production Ready
