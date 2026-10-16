# Million Istig‘for

Telegram WebApp: jamoaviy istig‘for (1 000 000 zikr va 1 000 000 faol soniya maqsadi).

## Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2 async, PostgreSQL, Alembic
- **Frontend:** Vue 3 (Composition API, JS), Pinia, Vue Router, Tailwind 3, Vite
- **Auth:** Telegram WebApp `initData` (server-side tekshiruv)

## Mahalliy ishga tushirish

### 1. Python

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env     # qiymatlarni to‘ldiring
alembic upgrade head
```

Muhim `.env` maydonlari:

| O‘zgaruvchi | Ma’nosi |
|-------------|---------|
| `DATABASE_URL` | PostgreSQL async URL |
| `TELEGRAM_BOT_TOKEN` | BotFather token |
| `DEBUG` | `true` faqat mahalliy |
| `DEV_TELEGRAM_ID` | Mahalliy dev user Telegram ID |
| `DISPLAY_TIMEZONE` | `Asia/Tashkent` — kunlik hissa |
| `ADMIN_TELEGRAM_IDS` | Vergul bilan admin Telegram ID lar (bo‘sh = admin yo‘q) |

### 2. Vue (development)

```bash
cd frontend
npm install
npm run dev
```

Vite `http://127.0.0.1:5173` — `/api` va `/static` FastAPI (`8000`) ga proxy qilinadi.  
`frontend/.env.development` da `VITE_DEV_MODE=1` (backend `DEBUG=true` bilan).

**Brauzerda `http://127.0.0.1:8000` (production build):** frontend avval `GET /api/config/client` dan `allow_dev_auth` oladi. Bu faqat backend `DEBUG=true` **va** `DEV_TELEGRAM_ID` o‘rnatilganda `true` — `import.meta.env.DEV` ga bog‘liq emas. Production (`DEBUG=false`) da doim `false`.

### 3. Vue (production — bitta origin)

```bash
cd frontend && npm run build
cd .. && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`frontend/dist` mavjud bo‘lsa, FastAPI Vue SPA ni `/`, `/welcome`, `/profile`, `/tasbeh`, `/admin` uchun serve qiladi.  
Dist yo‘q bo‘lsa, eski Jinja `/` ishlaydi.

### 4. Admin kirish

1. `.env` da `ADMIN_TELEGRAM_IDS=123456789` (o‘z Telegram ID ingiz).
2. Bot orqali WebApp oching (initData bilan).
3. `/admin` — frontend guard + **barcha** `/api/admin/*` serverda `require_admin`.

## Testlar

```bash
pytest tests/test_telegram_auth.py
# PostgreSQL bilan idempotency:
pytest tests/test_sync_idempotency.py
```

## Migratsiyalar

| Revision | Mazmun |
|----------|--------|
| `001_initial_schema` | Asosiy jadvalar |
| `002_onboarding` | Profil |
| `003_retention` | Tashrif snapshot maydonlari |
| `004_sync_visits_admin` | Sync batch idempotency, visits, kunlik hissa, faol sessiya indeksi |

Kunlik statistika cheklovlari: [docs/DAILY_STATS.md](docs/DAILY_STATS.md)

## API (qisqa)

| Method | Path |
|--------|------|
| GET | `/api/me` (+ `is_admin`) |
| POST | `/api/profile/onboarding` |
| POST | `/api/session/start` · `/stop` |
| POST | `/api/tasbeh/sync` (+ ixtiyoriy `batch_id` UUID) |
| POST | `/api/visit/heartbeat` · `/snapshot` |
| GET | `/api/admin/overview` · `/users` · `/daily` · `/funnel` |

## Railway

Production image: **`Dockerfile`** (Node 20 Vue build + Python 3.12 FastAPI). Railway: `railway.toml` → `builder = "DOCKERFILE"`.

| Bosqich | Buyruq |
|---------|--------|
| Build | Dockerfile multi-stage |
| Release | `alembic upgrade head` (Release Command — start ichida emas) |
| Start | Image CMD: `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

Batafsil: [docs/RAILWAY_VUE_DEPLOY.md](docs/RAILWAY_VUE_DEPLOY.md)

`DEBUG=false`, `ADMIN_TELEGRAM_IDS` production adminlar uchun.

Telegram bot: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBAPP_URL`, `TELEGRAM_WEBHOOK_BASE_URL` (public URL), ixtiyoriy `TELEGRAM_WEBHOOK_SECRET`. Batafsil: [docs/TELEGRAM_BOT.md](docs/TELEGRAM_BOT.md).

## Loyiha tuzilmasi

```
app/           # FastAPI
frontend/      # Vue SPA
alembic/
tests/
docs/
```

Eski `app/templates` va `app/static/js` reference sifatida qoldirilgan; production SPA `frontend/dist` orqali.
