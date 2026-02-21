import uuid
from datetime import datetime

from sqlalchemy import String, Text, ForeignKey, DateTime, Boolean, func, JSON, Uuid, ARRAY, TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StringArray(TypeDecorator):
    """A type that uses ARRAY(String) on PostgreSQL and JSON on other backends."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(ARRAY(String))
        return dialect.type_descriptor(JSON)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # kebab-case
    display_name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("categories.id"), nullable=True)
    tags: Mapped[list[str]] = mapped_column(StringArray, default=list)
    team_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("teams.id"), nullable=True)
    author_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"))
    visibility: Mapped[str] = mapped_column(String(20), default="public")  # public / team / private
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    author = relationship("User", back_populates="skills")
    team = relationship("Team", back_populates="skills")
    category = relationship("Category")
    versions = relationship("SkillVersion", back_populates="skill", order_by="SkillVersion.created_at.desc()")


class SkillVersion(Base):
    __tablename__ = "skill_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    skill_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("skills.id", ondelete="CASCADE"))
    version: Mapped[str] = mapped_column(String(50))  # semver
    content: Mapped[str] = mapped_column(Text)  # SKILL.md full text
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    changelog: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    skill = relationship("Skill", back_populates="versions")
    files = relationship("SkillFile", back_populates="version", cascade="all, delete-orphan")


class SkillFile(Base):
    __tablename__ = "skill_files"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    skill_version_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("skill_versions.id", ondelete="CASCADE"))
    path: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    file_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    version = relationship("SkillVersion", back_populates="files")
