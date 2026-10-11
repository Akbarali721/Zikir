from fastapi import APIRouter, HTTPException

from app.api.deps import CurrentUser, DbSession
from app.schemas.profile import OnboardingProfileRequest, OnboardingProfileResponse
from app.services.profile_service import complete_onboarding

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.post("/onboarding", response_model=OnboardingProfileResponse)
async def profile_onboarding(
    body: OnboardingProfileRequest,
    db: DbSession,
    user: CurrentUser,
) -> OnboardingProfileResponse:
    try:
        complete_onboarding(user, body.display_name, body.age)
        await db.flush()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to save profile") from exc

    return OnboardingProfileResponse(
        display_name=user.display_name,
        age=user.age,
        onboarding_completed=user.onboarding_completed,
    )
