"""Module registry schema (domain-expert answers): extend modules + axis_module_map, add registry_meta.

Idempotent: checks existing columns/tables via the inspector, so it is safe to run on a fresh DB
(where create_all already made the new columns) or an older one. SQLite-safe (uses batch mode).

Revision ID: 0002_module_registry
Revises: 0001_add_learned
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0002_module_registry"
down_revision = "0001_add_learned"
branch_labels = None
depends_on = None

_MODULE_COLS = {
    "name_th": sa.String(200),
    "phytocore_code": sa.String(120),
    "product_id": sa.Integer(),
    "dose_type": sa.String(16),
    "status": sa.String(16),
    "replaced_by": sa.String(32),
    "registry_version": sa.String(32),
    "contraindications": sa.Text(),
}


def _cols(insp, table):
    return {c["name"] for c in insp.get_columns(table)} if insp.has_table(table) else set()


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if insp.has_table("modules"):
        have = _cols(insp, "modules")
        for name, typ in _MODULE_COLS.items():
            if name not in have:
                op.add_column("modules", sa.Column(name, typ, nullable=True))

    if insp.has_table("axis_module_map") and "role" not in _cols(insp, "axis_module_map"):
        op.add_column("axis_module_map", sa.Column("role", sa.String(16), nullable=True))

    if not insp.has_table("registry_meta"):
        op.create_table(
            "registry_meta",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("registry_version", sa.String(32), nullable=True),
            sa.Column("framework_version", sa.String(32), nullable=True),
            sa.Column("effective_date", sa.String(32), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    if insp.has_table("registry_meta"):
        op.drop_table("registry_meta")
    if insp.has_table("axis_module_map") and "role" in _cols(insp, "axis_module_map"):
        with op.batch_alter_table("axis_module_map") as b:
            b.drop_column("role")
    if insp.has_table("modules"):
        have = _cols(insp, "modules")
        with op.batch_alter_table("modules") as b:
            for name in _MODULE_COLS:
                if name in have:
                    b.drop_column(name)
