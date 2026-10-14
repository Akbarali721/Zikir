# Railway: Vue production (SPA)

## Muammo (sabab)

`app/main.py` **`frontend/dist/index.html` bo‘lsa** Vue SPA beradi, **bo‘lmasa** `app/api/web.py` → Jinja (`profile.css`, `/static/js/...`).

`frontend/dist` **gitignore** da — repoda yo‘q. Railway faqat `uvicorn` ishga tushirsa, **dist build qilinmaydi** → productionda eski HTML.

## Yechim

Deploy **build** bosqichida:

```bash
npm ci --prefix frontend
npm run build --prefix frontend
```

Repoda: `nixpacks.toml` (Nixpacks avtomatik qo‘llaydi).

## Railway Dashboard

| Sozlam | Qiymat |
|--------|--------|
| **Root Directory** | `/` (repo ildizi) |
| **Build** | Nixpacks (`nixpacks.toml`) |
| **Release Command** | `alembic upgrade head` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Watch Paths** | ixtiyoriy: `app/**`, `frontend/**` |

## Environment

- `DATABASE_URL` — PostgreSQL (asyncpg normalize qilinadi)
- `DEBUG=false`
- `TELEGRAM_WEBAPP_URL=https://zikir-production.up.railway.app/`
- Web servis: `TELEGRAM_BOT_MODE=off` (bot alohida worker bo‘lsa)

## Tekshiruv (deploy dan keyin)

1. View Source: `<script ... src="/assets/index-....js">` bo‘lishi kerak.
2. **`/static/css/profile.css`** bo‘lmasligi kerak (legacy).
3. `/tasbeh`, `/admin` — bir xil SPA `index.html`.

## Mahalliy (production kabi)

```powershell
cd frontend
npm ci
npm run build
cd ..
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
