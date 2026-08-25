"""Phase B — auth / RBAC / audit: ownership + tenant scope on reports, richer audit rows.

Adds (all nullable, additive — safe on fresh or existing DBs):
  reports.owner_clinician_id, reports.owner_case_subject, reports.clinic_id
  audit_log.role, audit_log.source, audit_log.request_id

Revision ID: 0004_auth_audit
Revises: 0003_learning_phase12
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_auth_audit"
down_revision = "0003_learning_phase12"
branch_labels = None
depends_on = None


def _has_col(insp, table: str, col: str) -> bool:
    try:
        return col in {c["name"] for c in insp.get_columns(table)}
    except Exception:  # noqa: BLE001
        return False


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    adds = [
        ("reports", "owner_clinician_id", sa.String(64)),
        ("reports", "owner_case_subject", sa.String(64)),
        ("reports", "clinic_id", sa.String(64)),
        ("audit_log", "role", sa.String(24)),
        ("audit_log", "source", sa.String(24)),
        ("audit_log", "request_id", sa.String(64)),
    ]
    for table, col, type_ in adds:
        if insp.has_table(table) and not _has_col(insp, table, col):
            op.add_column(table, sa.Column(col, type_, nullable=True))


def downgrade() -> None:
    for table, col in [
        ("reports", "owner_clinician_id"), ("reports", "owner_case_subject"),
        ("reports", "clinic_id"), ("audit_log", "role"),
        ("audit_log", "source"), ("audit_log", "request_id"),
    ]:
        try:
            op.drop_column(table, col)
        except Exception:  # noqa: BLE001
            pass
