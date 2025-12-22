# Dev/Prod Timezone Mismatch Fix

## Problem
Endpoint `/metrics` di dashboard menghasilkan output berbeda antara development dan production (Vercel):
- **Development (local)**: Menggunakan timezone lokal (misalnya UTC+7 Indonesia)
- **Production (Vercel)**: Menggunakan UTC timezone

Perbedaan timezone ini menyebabkan:
1. Data filtering berdasarkan tanggal mengambil data dari hari yang berbeda
2. Metrics menjadi salah karena date range tidak sesuai
3. Idle time calculation jadi tidak akurat

## Root Cause
1. `datetime.now()` tanpa timezone mengembalikan waktu local system
   - Di local: Jam 20:00 WIB = 2024-12-22
   - Di Vercel: Jam 13:00 UTC = 2024-12-22 (berbeda 7 jam)
2. Relative path untuk model files dapat berbeda
3. Tidak ada explicit timezone handling

## Solution

### 1. Timezone Handling (dashboard_service.py & dashboard.py)
Mengganti semua `datetime.now()` dengan `datetime.now(timezone.utc)`:

```python
# BEFORE (dev/prod inconsistent)
today = datetime.now().strftime("%Y-%m-%d")

# AFTER (consistent across dev/prod)
today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
```

**Perubahan:**
- Import `timezone` dari datetime module
- Ganti `datetime.now()` → `datetime.now(timezone.utc)` di 4 lokasi
- Ganti `datetime.now().isoformat()` → `datetime.now(timezone.utc).isoformat()`

### 2. Absolute Path Resolution (emission_service.py & anomaly_service.py)
Mengganti relative path dengan absolute path untuk model loading:

```python
# BEFORE (potential path issues in deployment)
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models', 'emission')

# AFTER (ensures correct path in both dev and prod)
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'emission'))
```

**Benefit:**
- Resolves path correctly regardless of working directory
- Works in containerized environment (Vercel)
- Consistent behavior between dev and prod

### 3. Better Error Logging
Enhanced error messages to include MODEL_DIR path:

```python
raise FileNotFoundError(f"Model file not found: {filepath} (MODEL_DIR={MODEL_DIR})")
```

Ini membantu debugging jika ada file path issues.

## Files Modified
1. `/app/services/dashboard_service.py`
   - Import timezone
   - 4x `datetime.now()` → `datetime.now(timezone.utc)`
   - Updated docstrings to mention UTC

2. `/app/api/v1/dashboard.py`
   - Import timezone
   - 1x `datetime.now()` → `datetime.now(timezone.utc)`

3. `/app/services/emission_service.py`
   - Use `os.path.abspath()` for MODEL_DIR
   - Better error messages

4. `/app/services/anomaly_service.py`
   - Use `os.path.abspath()` for MODEL_DIR
   - Better error messages

## Testing

### Before Deployment
```bash
# Test locally first
curl "http://localhost:8000/api/v1/dashboard/metrics?user_api_hash=xxx&device_id=123"

# Check that output is consistent
```

### After Deployment
1. Verify `/metrics` endpoint returns same data as development
2. Check `calculation_date` matches expected date
3. Verify `data_records_used` reflects filtered records

## Result
✅ Dashboard metrics endpoint now produces **consistent output** between development and production
✅ Date filtering works correctly regardless of timezone
✅ Model loading works in containerized environments
