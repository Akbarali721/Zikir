from pydantic import BaseModel, Field, field_validator


class OnboardingProfileRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=50)
    age: int = Field(ge=10, le=100)

    @field_validator("display_name")
    @classmethod
    def normalize_display_name(cls, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 2:
            raise ValueError("display_name must be at least 2 characters")
        if len(trimmed) > 50:
            raise ValueError("display_name must be at most 50 characters")
        return trimmed


class OnboardingProfileResponse(BaseModel):
    display_name: str
    age: int
    onboarding_completed: bool
