"""Initial migration - create all tables

Revision ID: 001
Revises:
Create Date: 2026-02-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Teams
    op.create_table(
        "teams",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Categories
    op.create_table(
        "categories",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("parent_id", UUID, sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Users
    op.create_table(
        "users",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("team_id", UUID, sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Skills
    op.create_table(
        "skills",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("category_id", UUID, sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("tags", JSON, nullable=True),
        sa.Column("team_id", UUID, sa.ForeignKey("teams.id"), nullable=True),
        sa.Column("author_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("visibility", sa.String(20), nullable=False, server_default="public"),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Skill Versions
    op.create_table(
        "skill_versions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("skill_id", UUID, sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("metadata_json", JSON, nullable=True),
        sa.Column("changelog", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Skill Files
    op.create_table(
        "skill_files",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("skill_version_id", UUID, sa.ForeignKey("skill_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("file_type", sa.String(50), nullable=True),
    )

    # API Keys
    op.create_table(
        "api_keys",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("scopes", JSON, nullable=True, server_default='["read"]'),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
    op.drop_table("skill_files")
    op.drop_table("skill_versions")
    op.drop_table("skills")
    op.drop_table("users")
    op.drop_table("categories")
    op.drop_table("teams")
