Project FastAPI minimal structure

Instruksi singkat:

1. Buat virtual environment dan install dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Jalankan server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. Endpoint contoh:
- Health: `/api/health`
- Root: `/`

Catatan: Sesuaikan `DATABASE_URL` di `.env` jika perlu.
