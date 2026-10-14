# Telegram bot integratsiyasi

Bot **aiogram 3** bilan FastAPI ichida ishlaydi. Foydalanuvchi WebApp dagi kabi **`telegram_id`** orqali `users` jadvalida aniqlanadi (`get_or_create_user`).

## Bot funksiyalari

| Harakat | Tavsif |
|---------|--------|
| `/start` | O‘zbekcha xush kelibsiz + inline tugmalar |
| 📿 Zikr qilish | Mavjud Vue WebApp (`TELEGRAM_WEBAPP_URL`) |
| 📊 Statistikam | Bugungi va jami **istig‘for** (`personal_*`, kunlik jadval) |
| 🏆 TOP-10 | Bugungi `user_daily_contributions` bo‘yicha 10 nafar (`leaderboard_opt_in=true`) |
| Reytingda ko‘rinish / chiqish | TOP-10 da chiqish roziligi |

## `.env` sozlamalari

| O‘zgaruvchi | Ma’nosi |
|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | BotFather token |
| `TELEGRAM_WEBAPP_URL` | WebApp manzili (HTTPS) |
| `TELEGRAM_WEBHOOK_BASE_URL` | Production: `https://<domain>` (pathsiz) |
| `TELEGRAM_WEBHOOK_SECRET` | **Majburiy** — `X-Telegram-Bot-Api-Secret-Token` |
| `TELEGRAM_BOT_ENABLED` | `false` bo‘lsa webhook ishlamaydi |

## Railway

1. Build/release o‘zgarishsiz: frontend build + `alembic upgrade head` + `uvicorn`.
2. Migratsiya: `006_leaderboard_opt_in`.
3. Env: yuqoridagi o‘zgaruvchilar; `TELEGRAM_WEBHOOK_BASE_URL` = Railway public URL.
4. BotFather: WebApp URL = `TELEGRAM_WEBAPP_URL`.
5. Server ishga tushganda `setWebhook` → `https://<domain>/api/telegram/webhook`.

## Mahalliy polling (tavsiya — `/start` tez tekshirish)

Batafsil: **[docs/BOT_LOCAL.md](BOT_LOCAL.md)**

```powershell
# .env: TELEGRAM_BOT_MODE=polling, TELEGRAM_BOT_TOKEN=..., DATABASE_URL=...
python -m app.bot.worker
```

## Mahalliy test (webhook)

### 1. Migratsiya

```powershell
cd d:\proekt\tasbeh
$env:PYTHONPATH="d:\proekt\tasbeh"
.venv\Scripts\alembic.exe upgrade head
```

### 2. Webhook (ngrok yoki Railway)

Production web servis: `TELEGRAM_BOT_MODE=webhook`.

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
ngrok http 8000
```

`.env`: `TELEGRAM_WEBHOOK_BASE_URL=https://xxxx.ngrok-free.app`, `TELEGRAM_WEBAPP_URL` ham HTTPS, `TELEGRAM_WEBHOOK_SECRET` — ixtiyoriy uzun random string.

### 3. Testlar

```powershell
pytest tests/test_telegram_bot.py tests/test_leaderboard_service.py -v
```

## API (WebApp)

`POST /api/profile/leaderboard-opt-in` — `{ "opt_in": true }` (Telegram initData auth bilan).

`GET /api/me` — `leaderboard_opt_in` maydoni qaytadi.
