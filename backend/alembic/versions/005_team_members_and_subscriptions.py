"""Add team_members and skill_subscriptions tables, drop users.team_id

Revision ID: 005
Revises: 004
Create Date: 2026-02-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create team_members table
    op.create_table(
        "team_members",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("team_id", sa.Uuid(), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(20), server_default="member", nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "team_id", name="uq_user_team"),
    )
    op.create_index("ix_team_members_user_id", "team_members", ["user_id"])
    op.create_index("ix_team_members_team_id", "team_members", ["team_id"])

    # Create skill_subscriptions table
    op.create_table(
        "skill_subscriptions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", sa.Uuid(), sa.ForeignKey("skills.id", ondelete="CASCADE"), nullable=False),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("subscribed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", "skill_id", name="uq_user_skill_subscription"),
    )
    op.create_index("ix_skill_subscriptions_user_id", "skill_subscriptions", ["user_id"])
    op.create_index("ix_skill_subscriptions_skill_id", "skill_subscriptions", ["skill_id"])

    # Migrate existing user->team relationships into team_members
    op.execute("""
        INSERT INTO team_members (id, user_id, team_id, role)
        SELECT gen_random_uuid(), id, team_id, 'member'
        FROM users
        WHERE team_id IS NOT NULL
    """)

    # Drop the old team_id column from users
    op.drop_column("users", "team_id")


def downgrade() -> None:
    # Re-add team_id column
    op.add_column("users", sa.Column("team_id", sa.Uuid(), sa.ForeignKey("teams.id"), nullable=True))

    # Migrate back: pick first team membership per user
    op.execute("""
        UPDATE users SET team_id = tm.team_id
        FROM (
            SELECT DISTINCT ON (user_id) user_id, team_id
            FROM team_members
            ORDER BY user_id, joined_at
        ) tm
        WHERE users.id = tm.user_id
    """)

    op.drop_table("skill_subscriptions")
    op.drop_table("team_members")
