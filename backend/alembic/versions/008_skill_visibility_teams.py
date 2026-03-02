"""Add skill_visibility_teams for multi-team visibility

Revision ID: 008
Revises: 007
Create Date: 2026-02-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "skill_visibility_teams",
        sa.Column("skill_id", sa.Uuid(), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.PrimaryKeyConstraint("skill_id", "team_id", name="pk_skill_visibility_teams"),
    )
    op.create_index("ix_skill_visibility_teams_skill_id", "skill_visibility_teams", ["skill_id"])
    op.create_index("ix_skill_visibility_teams_team_id", "skill_visibility_teams", ["team_id"])

    # Backfill: existing team-visibility skills with non-null team_id become single-item visibility set.
    op.execute(
        """
        INSERT INTO skill_visibility_teams (skill_id, team_id)
        SELECT s.id, s.team_id
        FROM skills s
        WHERE s.visibility = 'team' AND s.team_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_skill_visibility_teams_team_id", table_name="skill_visibility_teams")
    op.drop_index("ix_skill_visibility_teams_skill_id", table_name="skill_visibility_teams")
    op.drop_table("skill_visibility_teams")
