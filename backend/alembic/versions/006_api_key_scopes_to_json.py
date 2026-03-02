"""Convert api_keys.scopes from varchar[] to json when needed

Revision ID: 006
Revises: 005
Create Date: 2026-02-27
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Older deployments may have scopes as varchar[].
    # Newer code expects JSON; convert only when the old type is present.
    op.execute(
        """
        DO $$
        DECLARE col_type text;
        BEGIN
          SELECT c.udt_name INTO col_type
          FROM information_schema.columns c
          WHERE c.table_schema = 'public'
            AND c.table_name = 'api_keys'
            AND c.column_name = 'scopes';

          IF col_type = '_varchar' THEN
            ALTER TABLE api_keys
            ALTER COLUMN scopes TYPE json
            USING array_to_json(COALESCE(scopes, ARRAY[]::varchar[]));
          END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    # Convert JSON back to varchar[] if needed.
    op.execute(
        """
        DO $$
        DECLARE col_type text;
        BEGIN
          SELECT c.udt_name INTO col_type
          FROM information_schema.columns c
          WHERE c.table_schema = 'public'
            AND c.table_name = 'api_keys'
            AND c.column_name = 'scopes';

          IF col_type = 'json' OR col_type = 'jsonb' THEN
            ALTER TABLE api_keys
            ALTER COLUMN scopes TYPE varchar[]
            USING ARRAY(
              SELECT jsonb_array_elements_text(COALESCE(scopes::jsonb, '[]'::jsonb))
            );
          END IF;
        END
        $$;
        """
    )
