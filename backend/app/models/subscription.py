import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, DateTime, func, Uuid, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class SkillSubscription(Base):
    __tablename__ = "skill_subscriptions"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_id", name="uq_user_skill_subscription"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"))
    skill_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("skills.id", ondelete="CASCADE"))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subscriptions")
    skill = relationship("Skill", back_populates="subscriptions")
