"""Add skill_usage_logs table

Revision ID: 003
Revises: 002
Create Date: 2026-02-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skill_usage_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("skill_id", sa.Uuid(), sa.ForeignKey("skills.id", ondelete="SET NULL"), nullable=True),
        sa.Column("skill_name", sa.String(100), nullable=False),
        sa.Column("skill_version", sa.String(50), nullable=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("api_key_id", sa.Uuid(), sa.ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_skill_usage_logs_created_at", "skill_usage_logs", ["created_at"])
    op.create_index("ix_skill_usage_logs_name_created", "skill_usage_logs", ["skill_name", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_skill_usage_logs_name_created", table_name="skill_usage_logs")
    op.drop_index("ix_skill_usage_logs_created_at", table_name="skill_usage_logs")
    op.drop_table("skill_usage_logs")
