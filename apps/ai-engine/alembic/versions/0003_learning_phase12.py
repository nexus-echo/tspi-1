"""Phase 12 — Adaptive Biological Intelligence Loop tables (3 levels + propose-only population).

Adds: patient_axis_weights, network_observations, patient_models, model_update_proposals,
learning_records. Idempotent (checks the inspector), safe on fresh or existing DBs.

Revision ID: 0003_learning_phase12
Revises: 0002_module_registry
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0003_learning_phase12"
down_revision = "0002_module_registry"
branch_labels = None
depends_on = None

_TABLES = ["patient_axis_weights", "network_observations", "patient_models",
           "model_update_proposals", "learning_records"]


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())

    if not insp.has_table("patient_axis_weights"):
        op.create_table(
            "patient_axis_weights",
            sa.Column("case_id", sa.String(64), primary_key=True),
            sa.Column("axis_code", sa.String(8), primary_key=True),
            sa.Column("weight", sa.Float, default=1.0),
            sa.Column("cumulative_adjustment", sa.Float, default=0.0),
            sa.Column("consecutive_improvements", sa.Integer, default=0),
            sa.Column("samples", sa.Integer, default=0),
            sa.Column("updated_at", sa.DateTime),
        )
    if not insp.has_table("network_observations"):
        op.create_table(
            "network_observations",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("case_id", sa.String(64)),
            sa.Column("changed_first", sa.String(64)),
            sa.Column("downstream", sa.String(64), nullable=True),
            sa.Column("direction", sa.String(16)),
            sa.Column("magnitude", sa.Float, nullable=True),
            sa.Column("time_to_response_days", sa.Integer, nullable=True),
            sa.Column("repeated", sa.Boolean, default=False),
            sa.Column("confounders", sa.Text, nullable=True),
            sa.Column("created_at", sa.DateTime),
        )
    if not insp.has_table("patient_models"):
        op.create_table(
            "patient_models",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("case_id", sa.String(64), index=True),
            sa.Column("version", sa.Integer, default=1),
            sa.Column("change_kind", sa.String(16), default="CONFIRM"),
            sa.Column("axis_state", sa.JSON),
            sa.Column("network_state", sa.JSON),
            sa.Column("trigger", sa.String(200), nullable=True),
            sa.Column("superseded", sa.Boolean, default=False),
            sa.Column("created_at", sa.DateTime),
        )
    if not insp.has_table("model_update_proposals"):
        op.create_table(
            "model_update_proposals",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("axis_code", sa.String(8)),
            sa.Column("current_weight", sa.Float, default=1.0),
            sa.Column("proposed_weight", sa.Float, default=1.0),
            sa.Column("sample_size", sa.Integer, default=0),
            sa.Column("improved", sa.Integer, default=0),
            sa.Column("worsened", sa.Integer, default=0),
            sa.Column("rationale", sa.Text, nullable=True),
            sa.Column("blocking_reasons", sa.Text, nullable=True),
            sa.Column("status", sa.String(24), default="PROPOSE_MODEL_UPDATE"),
            sa.Column("reviewed_by", sa.String(64), nullable=True),
            sa.Column("review_date", sa.DateTime, nullable=True),
            sa.Column("created_at", sa.DateTime),
        )
    if not insp.has_table("learning_records"):
        op.create_table(
            "learning_records",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("case_id", sa.String(64), index=True),
            sa.Column("patient_model_version", sa.Integer, nullable=True),
            sa.Column("baseline_axis_state", sa.JSON),
            sa.Column("baseline_network_state", sa.JSON),
            sa.Column("followup_axis_state", sa.JSON),
            sa.Column("followup_network_state", sa.JSON),
            sa.Column("intervention_modules", sa.JSON),
            sa.Column("dose", sa.String(120), nullable=True),
            sa.Column("duration", sa.String(64), nullable=True),
            sa.Column("adherence", sa.String(32), nullable=True),
            sa.Column("lifestyle_interventions", sa.JSON),
            sa.Column("concurrent_medications", sa.JSON),
            sa.Column("symptom_response", sa.Text, nullable=True),
            sa.Column("laboratory_response", sa.Text, nullable=True),
            sa.Column("adverse_response", sa.Text, nullable=True),
            sa.Column("time_to_response", sa.String(64), nullable=True),
            sa.Column("confounders", sa.JSON),
            sa.Column("physician_interpretation", sa.Text, nullable=True),
            sa.Column("learning_approval_status", sa.String(24), default="UNREVIEWED"),
            sa.Column("created_at", sa.DateTime),
        )


def downgrade() -> None:
    insp = sa.inspect(op.get_bind())
    for t in reversed(_TABLES):
        if insp.has_table(t):
            op.drop_table(t)
