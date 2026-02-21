import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, DateTime, Index, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SkillUsageLog(Base):
    __tablename__ = "skill_usage_logs"
    __table_args__ = (
        Index("ix_skill_usage_logs_name_created", "skill_name", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("skills.id", ondelete="SET NULL"), nullable=True
    )
    skill_name: Mapped[str] = mapped_column(String(100))
    skill_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    api_key_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(20))  # "resolve" | "raw" | "catalog"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
