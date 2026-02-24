import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="member")  # admin / member
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("SkillSubscription", back_populates="user", cascade="all, delete-orphan")
    skills = relationship("Skill", back_populates="author")
    api_keys = relationship("ApiKey", back_populates="user")
