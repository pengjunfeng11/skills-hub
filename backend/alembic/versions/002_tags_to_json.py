"""Change tags column from varchar[] to json

Revision ID: 002
Revises: 001
Create Date: 2026-02-21
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert varchar[] to json, preserving existing data
    op.execute("""
        ALTER TABLE skills
        ALTER COLUMN tags TYPE json
        USING array_to_json(COALESCE(tags, ARRAY[]::varchar[]))
    """)


def downgrade() -> None:
    # Convert json back to varchar[]
    op.execute("""
        ALTER TABLE skills
        ALTER COLUMN tags TYPE varchar[]
        USING ARRAY(SELECT jsonb_array_elements_text(tags::jsonb))
    """)
