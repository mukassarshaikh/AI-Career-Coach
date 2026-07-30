"""Add ivfflat vector indexes on market_skill_reference and skill_vectors

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-29
"""

from typing import Sequence, Union
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ivfflat index on market_skill_reference.vector for cosine distance searches (<=>)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_market_skill_reference_vector_ivfflat "
        "ON market_skill_reference USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);"
    )

    # Create ivfflat index on skill_vectors.vector for cosine distance searches (<=>)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_skill_vectors_vector_ivfflat "
        "ON skill_vectors USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_skill_vectors_vector_ivfflat;")
    op.execute("DROP INDEX IF EXISTS ix_market_skill_reference_vector_ivfflat;")
