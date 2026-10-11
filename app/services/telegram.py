import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.models.user import User


def validate_webapp_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict:
    """
    Validate Telegram WebApp initData per official docs.
    Returns parsed user dict from the 'user' field.
    """
    if not init_data or not bot_token:
        raise HTTPException(status_code=401, detail="Telegram authentication required")

    # parse_qsl allaqachon URL-decode qiladi; qayta unquote ikkinchi marta buzadi.
    pairs = parse_qsl(init_data, keep_blank_values=True)
    data = dict(pairs)
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Invalid Telegram initData: missing hash")

    auth_date = data.get("auth_date")
    if not auth_date:
        raise HTTPException(status_code=401, detail="Invalid Telegram initData: missing auth_date")
    try:
        auth_ts = int(auth_date)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid auth_date") from exc
    now_ts = int(time.time())
    if auth_ts > now_ts + 300:
        raise HTTPException(status_code=401, detail="Telegram initData auth_date in the future")
    if now_ts - auth_ts > max_age_seconds:
        raise HTTPException(status_code=401, detail="Telegram initData expired")

    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated, received_hash):
        raise HTTPException(status_code=401, detail="Invalid Telegram initData signature")

    user_raw = data.get("user")
    if not user_raw:
        raise HTTPException(status_code=401, detail="Telegram user missing in initData")

    try:
        user_data = json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid Telegram user payload")

    if "id" not in user_data:
        raise HTTPException(status_code=401, detail="Invalid Telegram user id")

    return user_data


async def get_or_create_user(session: AsyncSession, tg_user: dict) -> User:
    telegram_id = int(tg_user["id"])
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    username = tg_user.get("username")
    first_name = tg_user.get("first_name")
    last_name = tg_user.get("last_name")

    if user is None:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        session.add(user)
        await session.flush()
    else:
        user.username = username
        user.first_name = first_name
        user.last_name = last_name

    return user


async def resolve_current_user(
    request: Request,
    session: AsyncSession,
    *,
    x_telegram_init_data: str | None,
    x_dev_mode: str | None,
) -> User:
    settings: Settings = get_settings()

    test_tid_raw = request.headers.get("X-Test-Telegram-Id")
    if settings.enable_integration_test_auth and test_tid_raw:
        try:
            test_tid = int(test_tid_raw.strip())
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid X-Test-Telegram-Id") from exc
        return await get_or_create_user(
            session,
            {
                "id": test_tid,
                "username": f"test_{test_tid}",
                "first_name": "Test",
                "last_name": str(test_tid)[-4:],
            },
        )

    if x_telegram_init_data:
        if not settings.telegram_bot_token:
            raise HTTPException(status_code=503, detail="Bot token not configured")
        tg_user = validate_webapp_init_data(x_telegram_init_data, settings.telegram_bot_token)
        return await get_or_create_user(session, tg_user)

    if settings.debug and settings.dev_telegram_id is not None:
        if x_dev_mode == "1" or request.query_params.get("dev") == "1":
            dev_user = {
                "id": settings.dev_telegram_id,
                "username": "dev_user",
                "first_name": "Dev",
                "last_name": "User",
            }
            return await get_or_create_user(session, dev_user)

    raise HTTPException(
        status_code=401,
        detail="Unauthorized: provide X-Telegram-Init-Data or enable DEV mode (DEBUG=true)",
    )
