"""Add allowed_tags and key_encrypted to api_keys

Revision ID: 004
Revises: 003
Create Date: 2026-02-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("api_keys", sa.Column("allowed_tags", sa.JSON(), server_default="[]", nullable=False))
    op.add_column("api_keys", sa.Column("key_encrypted", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("api_keys", "key_encrypted")
    op.drop_column("api_keys", "allowed_tags")
