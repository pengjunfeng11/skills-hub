"""Add skill_edit_logs table

Revision ID: 007
Revises: 006
Create Date: 2026-02-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skill_edit_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("skill_id", sa.Uuid(), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("target_type", sa.String(20), nullable=False, server_default="skill"),
        sa.Column("target_path", sa.String(500), nullable=True),
        sa.Column("from_version", sa.String(50), nullable=True),
        sa.Column("to_version", sa.String(50), nullable=True),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_skill_edit_logs_skill_created", "skill_edit_logs", ["skill_id", "created_at"])
    op.create_index("ix_skill_edit_logs_actor_created", "skill_edit_logs", ["actor_user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_skill_edit_logs_actor_created", table_name="skill_edit_logs")
    op.drop_index("ix_skill_edit_logs_skill_created", table_name="skill_edit_logs")
    op.drop_table("skill_edit_logs")
