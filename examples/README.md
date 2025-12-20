# Request Body Examples - Emission Prediction & Anomaly Detection APIs

Folder ini berisi contoh-contoh lengkap untuk menggunakan kedua endpoint API:
1. **Emission Prediction** - Prediksi emisi CO2 berdasarkan aggregated hourly data
2. **Anomaly Detection** - Deteksi anomali perjalanan secara real-time dan daily reports

## 📁 File Structure

```
examples/
├── emission_prediction_request.json      # 5+ contoh request bodies untuk emission prediction
├── anomaly_detection_request.json        # 8+ contoh request bodies untuk anomaly detection
├── curl_examples.sh                      # Shell script dengan curl commands
├── python_integration_examples.py        # Python client dengan 15+ contoh
└── README.md                             # File ini
```

## 🚀 Quick Start

### 1. Menggunakan Curl (Langsung dari Terminal)

```bash
# Clone repo dan masuk ke folder examples
cd examples

# Jalankan semua curl examples
bash curl_examples.sh
```

### 2. Menggunakan Python

```bash
# Install dependencies (jika belum)
pip install requests

# Jalankan semua contoh
python python_integration_examples.py
```

### 3. Menggunakan JSON Files Langsung

Buka `emission_prediction_request.json` atau `anomaly_detection_request.json` dan copy-paste contohnya ke:
- Postman
- Insomnia
- Thunder Client
- atau HTTP client favorit Anda

## 📊 Endpoint Details

### Emission Prediction Endpoint
```
POST /api/v1/emission/predict-hourly
Content-Type: application/json
```

**Input:** 12 aggregated hourly features
**Output:** 2 predictions (CO2 grams/hour & intensity g/km)

**Contoh Request:**
```json
{
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
}
```

**Contoh Response:**
```json
{
  "co2_grams_total": 2850.45,
  "co2_intensity_mean": 63.12,
  "unit_emissions": "grams/hour",
  "unit_intensity": "g/km"
}
```

### Anomaly Detection Endpoint (Real-time)
```
POST /api/v1/anomaly/detect
Content-Type: application/json
```

**Input:** 8 real-time features per record
**Output:** Anomaly detection result dengan severity level

**Contoh Request:**
```json
{
  "speed": 60.0,
  "distance_delta": 1.2,
  "fuel_delta": -0.3,
  "fuel_consumption_rate": 0.25,
  "idle_duration": 0,
  "rpm": 1800,
  "engine_load": 50.0,
  "co2_intensity": 42.5
}
```

**Contoh Response:**
```json
{
  "is_anomaly": false,
  "anomaly_score": 0.15,
  "anomaly_types": [],
  "severity": "LOW",
  "fuel_theft_flag": false,
  "emission_inefficiency_flag": false,
  "excessive_idle_flag": false,
  "ml_anomaly_flag": false,
  "fuel_theft_risk_score": 0,
  "emission_risk_score": 0.2
}
```

### Anomaly Detection Daily Report Endpoint
```
POST /api/v1/anomaly/daily-report
Content-Type: application/json
```

**Input:** Daily aggregated metrics untuk excessive idle detection
**Output:** Daily anomaly analysis dengan excessive idle detection

**Contoh Request:**
```json
{
  "total_idle_minutes": 240,
  "total_distance_km": 125.5,
  "total_fuel_consumed_liters": 8.3,
  "average_co2_intensity": 55.2,
  "max_co2_intensity": 180.0,
  "total_harsh_accelerations": 3,
  "total_harsh_brakes": 2,
  "device_id": "VHCL001",
  "report_date": "2024-01-15"
}
```

## 📋 Contoh Skenario

### Emission Prediction Examples

| Scenario | File | Karakteristik | Use Case |
|----------|------|---------------|----------|
| Normal Driving | `example_2_normal_driving` | Speed 60 km/h, idle minimal | Baseline comparison |
| City Traffic | `example_3_excessive_fuel_consumption` | Speed tinggi, consumption tinggi | Monitor urban driving |
| High Emission | `example_4_high_emission_inefficiency` | co2_intensity 150 | Detect problem vehicles |
| Excessive Idle | `example_5_excessive_idling` | idle 15 min, speed 0 | Fleet optimization |

### Anomaly Detection Examples

| Anomaly Type | File | Triggers | Severity |
|--------------|------|----------|----------|
| Fuel Theft | `example_1_fuel_theft_detected` | fuel_delta < -5, speed=0 | CRITICAL |
| Emission Inefficiency | `example_4_high_emission_inefficiency` | co2_intensity > 2-sigma | HIGH |
| Excessive Idling | `example_5_excessive_idling` | idle_duration > threshold | MEDIUM |
| ML Anomaly | `example_7_multiple_anomalies` | Isolation Forest score < 0 | VARIABLE |

## 🔍 Feature Guide

### Emission Prediction Features

| Feature | Range | Unit | Description |
|---------|-------|------|-------------|
| `speed_mean` | 0-200 | km/h | Rata-rata kecepatan dalam jam |
| `speed_max` | 0-200 | km/h | Kecepatan maksimal dalam jam |
| `speed_std` | 0-100 | km/h | Standard deviation kecepatan |
| `distance_delta_total` | 0-200 | km | Total jarak tempuh dalam jam |
| `rpm_mean` | 0-3000 | RPM | Rata-rata RPM mesin |
| `rpm_max` | 0-3000 | RPM | RPM maksimal dalam jam |
| `engine_load_mean` | 0-100 | % | Rata-rata beban mesin |
| `is_moving_mean` | 0-1 | ratio | Proporsi waktu kendaraan bergerak |
| `is_idle_total` | 0-60 | minutes | Total durasi idle dalam jam |
| `hour` | 0-23 | hour | Jam perjalanan (0=midnight, 12=noon) |
| `day_of_week` | 0-6 | day | Hari minggu (0=Monday, 6=Sunday) |
| `is_weekend` | 0-1 | binary | 1 jika weekend, 0 jika weekday |

### Anomaly Detection Features

| Feature | Range | Unit | Description |
|---------|-------|------|-------------|
| `speed` | 0-200 | km/h | Kecepatan saat ini |
| `distance_delta` | 0-200 | km | Jarak sejak record sebelumnya |
| `fuel_delta` | -50 to +50 | L | Perubahan fuel level (- = konsumsi) |
| `fuel_consumption_rate` | 0-2 | L/km | Konsumsi per km |
| `idle_duration` | 0-1440 | minutes | Durasi idle dalam record |
| `rpm` | 0-3000 | RPM | RPM mesin saat ini |
| `engine_load` | 0-100 | % | Beban mesin dalam persen |
| `co2_intensity` | 0-1000 | g/km | Emisi CO2 per kilometer |

## 🎯 Anomaly Detection Rules

### 1. Fuel Theft Detection
```
Triggers:
  - fuel_delta < -5.0 (drop > 5 liter)
  - speed = 0 (kendaraan diam)
  - distance_delta < 0.1 (tidak ada pergerakan)
```

### 2. Emission Inefficiency Detection
```
Triggers:
  - co2_intensity > mean + 2*std
  - Threshold dinamis berdasarkan historical data
```

### 3. Excessive Idle Detection (Daily)
```
Triggers:
  - total_idle_minutes > 120 per hari
  - Dideteksi via /daily-report endpoint
```

### 4. ML-based Anomaly (Isolation Forest)
```
Triggers:
  - Isolation Forest score < 0
  - Mendeteksi pola abnormal dari kombinasi features
```

## 💡 Tips & Best Practices

### Untuk Emission Prediction
1. **Aggregation**: Features harus di-aggregate per jam dari raw data
2. **Hour Parameter**: Gunakan nilai 0-23 untuk pattern detection (rush hour vs night)
3. **Validation**: Pastikan semua nilai numerik (float/int)
4. **Comparison**: Gunakan hasil untuk trending dan benchmarking

### Untuk Anomaly Detection
1. **Real-time Processing**: /detect endpoint untuk record-by-record monitoring
2. **Daily Aggregation**: /daily-report untuk excessive idle detection
3. **Severity Level**: 
   - `CRITICAL`: Immediate action required (fuel theft)
   - `HIGH`: Strong anomaly signals (multiple flags)
   - `MEDIUM`: Single anomaly detected
   - `LOW`: Warning signs but not critical

4. **Risk Scores**: 0-1 scale, semakin tinggi = semakin berisiko

## 🛠️ Integration Patterns

### Batch Processing
```python
# Lihat python_integration_examples.py untuk contoh lengkap
results = batch_emission_predictions(records_list)
```

### Real-time Monitoring
```python
# Monitor setiap record yang masuk
result = anomaly_client.detect_normal_operation()
if result['is_anomaly']:
    alert_user()
```

### Health Monitoring
```python
# Comprehensive health check
health = monitor_vehicle_health(device_id, records)
generate_report(health)
```

## 📝 Usage Examples

### Dengan Postman

1. Buat request baru (POST)
2. URL: `http://localhost:8000/api/v1/emission/predict-hourly`
3. Headers: `Content-Type: application/json`
4. Body: Pilih "raw" → copy-paste dari `emission_prediction_request.json`
5. Click "Send"

### Dengan VS Code REST Client

Buat file `test.http`:
```http
POST http://localhost:8000/api/v1/emission/predict-hourly
Content-Type: application/json

{
  "speed_mean": 60.0,
  "speed_max": 90.0,
  ...
}
```

### Dengan NodeJS

```javascript
const response = await fetch('http://localhost:8000/api/v1/emission/predict-hourly', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    speed_mean: 60.0,
    // ... features
  })
});
const result = await response.json();
```

## 🔗 Related Documentation

- API Documentation: `../docs/API_SPECIFICATION.md`
- Model Details: `../docs/MODEL_INTEGRATION_GUIDE.md`
- Architecture: `../docs/ARCHITECTURE_OVERVIEW.md`

## ❓ FAQ

**Q: Berapa banyak request yang bisa dihandle?**
A: Sistem dirancang untuk ribuan request per jam. Untuk load testing, gunakan bash script atau Python batching.

**Q: Bagaimana jika ada error?**
A: Cek response status code:
- 200: Success
- 400: Invalid input (check feature values and types)
- 422: Validation error (missing required fields)
- 500: Server error (check logs)

**Q: Bisa batch request?**
A: Saat ini per-request. Untuk batch, loop melalui records (lihat `python_integration_examples.py`).

**Q: Model accuracy?**
A: Check `../docs/` untuk model performance metrics dan validation results.

---

**Last Updated:** 2024
**Version:** 1.0
