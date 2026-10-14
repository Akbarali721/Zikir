# Botni mahalliy polling bilan ishlatish

## Nega `/start` javob bermaydi?

Ko‘pincha uchta sabab:

1. **Webhook yoqilgan, lekin xato** — Railway’da `setWebhook` bor, lekin `/api/telegram/webhook` 403/503 qaytaradi (masalan, `TELEGRAM_WEBHOOK_SECRET` mos kelmasa). Telegram yangilanish yuboradi, javob yo‘q — bot «jim».
2. **Webhook boshqa URL da** — eski deploy URL yoki noto‘g‘ri domen.
3. **Polling + webhook bir vaqt** — mahalliy polling ishlatayapsiz, lekin Telegram hali production webhook ga yuboradi. **Polling boshlashdan oldin webhook o‘chirilishi kerak** (`delete_webhook` — worker avtomatik qiladi).

Handlerlar (`app/bot/handlers.py`) odatda sog‘lom; muammo **yangilanish yetib kelmasligi** da.

---

## `.env` (mahalliy polling)

```env
DATABASE_URL=postgresql+asyncpg://...@...   # Railway Postgres URL ham bo‘lishi mumkin
TELEGRAM_BOT_TOKEN=<BotFather token>
TELEGRAM_WEBAPP_URL=https://zikir-production.up.railway.app/
TELEGRAM_BOT_MODE=polling
TELEGRAM_BOT_ENABLED=true
```

**Mahalliy polling paytida** web servisda `TELEGRAM_BOT_MODE=webhook` qoldirmang — ikkalasi webhook ni qayta o‘rnatishi mumkin.

WebApp (Vue) alohida Railway’da qolishi mumkin; bot faqat tugma orqali shu URL ni ochadi.

---

## Ishga tushirish

```powershell
cd d:\proekt\tasbeh
$env:PYTHONPATH="d:\proekt\tasbeh"
.venv\Scripts\python.exe -m app.bot.worker
```

Yoki:

```powershell
.venv\Scripts\python.exe scripts\run_telegram_bot_polling.py
```

Telegram’da @MillionIstigforBot ga `/start` yuboring.

---

## Railway worker (eslatmalar bilan)

| Servis | `TELEGRAM_BOT_MODE` | Start buyruq |
|--------|---------------------|--------------|
| Web (Vue + API) | `off` | `uvicorn app.main:app ...` |
| Bot worker | `polling` | `python -m app.bot.worker` |

**Faqat bittasi:** webhook **yoki** polling. Eslatmalar (07:00 / 22:00 Toshkent) **faqat polling worker** da ishlaydi.

Bot tugmalari: Zikr qilish, Statistikam, TOP-10, reyting, **Eslatmalarni yoqish/o‘chirish** (default OFF).

---

## Testlar

```powershell
pytest tests/test_bot_polling_mode.py tests/test_telegram_bot.py -v
```
