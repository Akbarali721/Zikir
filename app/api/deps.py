import uuid
from typing import Annotated

from fastapi import Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.models.user import User
from app.services.telegram import resolve_current_user


def parse_visit_header(x_visit_id: str | None) -> uuid.UUID | None:
    if not x_visit_id:
        return None
    try:
        return uuid.UUID(x_visit_id.strip())
    except ValueError:
        return None


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    x_telegram_init_data: Annotated[str | None, Header(alias="X-Telegram-Init-Data")] = None,
    x_dev_mode: Annotated[str | None, Header(alias="X-Dev-Mode")] = None,
) -> User:
    return await resolve_current_user(
        request,
        session,
        x_telegram_init_data=x_telegram_init_data,
        x_dev_mode=x_dev_mode,
    )


DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
