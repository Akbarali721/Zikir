# Deploy oldi tekshiruv

## Asosiy baza (Akbarali saqlanadi)

```powershell
cd d:\proekt\tasbeh
$env:PYTHONPATH="d:\proekt\tasbeh"
.venv\Scripts\python.exe scripts\snapshot_main_users.py
```

Test oqimi **faqat** `million_istighfor_test` bazasida.

## Test bazasi

```powershell
$env:PYTHONPATH="d:\proekt\tasbeh"
.venv\Scripts\python.exe scripts\ensure_test_db.py
$env:TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/million_istighfor_test"
.venv\Scripts\python.exe -m pytest tests/test_integration_parallel.py -v
```

## Mahalliy brauzer oqimi (asosiy DB + DEV)

Terminal 1: `uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`  
`.env`: `DEBUG=true`, `DEV_TELEGRAM_ID=...`

Terminal 2 (ixtiyoriy yangi build): `cd frontend && npm run build`

URL: **http://127.0.0.1:8000/**

Yangi DEV foydalanuvchi uchun onboardingni SQL bilan nol qilish (faqat dev ID):

```sql
UPDATE users SET onboarding_completed=false, display_name=NULL, age=NULL
WHERE telegram_id = <DEV_TELEGRAM_ID>;
```

## Vite dev

**http://127.0.0.1:5173/** + backend 8000

## Integration auth

`ENABLE_INTEGRATION_TEST_AUTH=1` faqat pytest `integration_env` fixture orqali test DB da. Production `.env.example` da yo‘q.
