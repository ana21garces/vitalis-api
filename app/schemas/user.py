from pydantic import BaseModel, EmailStr
from uuid import UUID
from datetime import datetime
from app.models.user import UserRole


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: str
    university: str | None
    program: str | None
    semester: int | None
    role: UserRole
    is_active: bool
    is_verified: bool
    total_xp: int
    current_level: int
    streak_days: int
    created_at: datetime

    model_config = {"from_attributes": True}