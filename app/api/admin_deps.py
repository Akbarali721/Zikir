from typing import Annotated

from fastapi import Depends, HTTPException

from app.api.deps import CurrentUser
from app.config import get_settings


def parse_admin_telegram_ids(raw: str) -> set[int]:
    ids: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.add(int(part))
        except ValueError:
            continue
    return ids


def is_user_admin(user) -> bool:
    settings = get_settings()
    allow = parse_admin_telegram_ids(settings.admin_telegram_ids)
    if not allow:
        return False
    return user.telegram_id in allow


async def require_admin(user: CurrentUser):
    if not is_user_admin(user):
        raise HTTPException(status_code=403, detail="Admin access denied")
    return user


AdminUser = Annotated[object, Depends(require_admin)]
