import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, Enum as SAEnum, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base
from sqlalchemy.orm import relationship
import enum


class UserRole(str, enum.Enum):
    STUDENT = "student"
    HEALTH_MANAGER = "health_manager"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    university = Column(String(150), nullable=True)
    program = Column(String(150), nullable=True)
    semester = Column(Integer, nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    total_xp = Column(Integer, default=0, nullable=False)
    current_level = Column(Integer, default=1, nullable=False)
    streak_days = Column(Integer, default=0, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    survey_responses = relationship("SurveyResponse", back_populates="user")

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"