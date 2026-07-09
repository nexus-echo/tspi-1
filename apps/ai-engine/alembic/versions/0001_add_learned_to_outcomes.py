"""add learned column to outcomes (Phase 4)

Idempotent: only adds the column if missing, so it is safe on both fresh databases (where
create_all already built it) and existing databases (where it was absent).

Revision ID: 0001_add_learned
Revises:
Create Date: 2026-06-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_add_learned"
down_revision = None
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    if table not in insp.get_table_names():
        return True  # table absent -> create_all will build it with the column
    return column in {c["name"] for c in insp.get_columns(table)}


def upgrade() -> None:
    if not _has_column("outcomes", "learned"):
        op.add_column("outcomes",
                      sa.Column("learned", sa.Boolean(), nullable=False, server_default=sa.false()))


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if "outcomes" in insp.get_table_names() and \
       "learned" in {c["name"] for c in insp.get_columns("outcomes")}:
        op.drop_column("outcomes", "learned")
