"""P4 — encrypted patient identity storage (PHI), keyed by case_id.

Revision ID: 0005_pii_identity
Revises: 0004_auth_audit
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0005_pii_identity"
down_revision = "0004_auth_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    if not insp.has_table("patient_identities"):
        op.create_table(
            "patient_identities",
            sa.Column("case_id", sa.String(64), primary_key=True),
            sa.Column("blob", sa.Text, nullable=False),
            sa.Column("encrypted", sa.Boolean, nullable=False, server_default=sa.true()),
            sa.Column("created_at", sa.DateTime),
            sa.Column("updated_at", sa.DateTime),
        )


def downgrade() -> None:
    try:
        op.drop_table("patient_identities")
    except Exception:  # noqa: BLE001
        pass
