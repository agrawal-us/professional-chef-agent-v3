"""Initial tables

Revision ID: 001
Revises:
Create Date: 2026-06-09
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "detection_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.String(),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("detection_model", sa.String(100)),
        sa.Column("prompt_version", sa.String(20)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_detection_logs_session_id", "detection_logs", ["session_id"])

    op.create_table(
        "generation_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "session_id",
            sa.String(),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("generation_model", sa.String(100)),
        sa.Column("generation_provider", sa.String(50)),
        sa.Column("prompt_version", sa.String(20)),
        sa.Column("user_feedback", sa.String(20)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_generation_logs_session_id", "generation_logs", ["session_id"])

    op.create_table(
        "prompt_versions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("prompt_name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("thumbs_up_rate", sa.Float()),
        sa.Column("sample_count", sa.Integer(), server_default="0"),
        sa.Column("notes", sa.Text()),
        sa.Column(
            "effective_date",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deprecated_date", sa.DateTime(timezone=True)),
    )


def downgrade() -> None:
    op.drop_table("prompt_versions")
    op.drop_table("generation_logs")
    op.drop_table("detection_logs")
    op.drop_table("sessions")
