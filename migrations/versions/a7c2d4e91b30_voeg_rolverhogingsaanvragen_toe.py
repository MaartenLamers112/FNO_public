"""Voeg rolverhogingsaanvragen toe.

Revision ID: a7c2d4e91b30
Revises: f3a91c7d4e62
"""

import sqlalchemy as sa
from alembic import op

revision = "a7c2d4e91b30"
down_revision = "f3a91c7d4e62"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Voeg de tabel voor rolverhogingsaanvragen toe."""

    op.create_table(
        "role_upgrade_request",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("requested_role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["reviewed_by_user_id"], ["user.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_role_upgrade_request_user_id",
        "role_upgrade_request",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_role_upgrade_request_status",
        "role_upgrade_request",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_role_upgrade_request_requested_at",
        "role_upgrade_request",
        ["requested_at"],
        unique=False,
    )
    op.create_index(
        "ix_role_upgrade_request_reviewed_by_user_id",
        "role_upgrade_request",
        ["reviewed_by_user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Verwijder de tabel voor rolverhogingsaanvragen."""

    op.drop_index(
        "ix_role_upgrade_request_reviewed_by_user_id",
        table_name="role_upgrade_request",
    )
    op.drop_index(
        "ix_role_upgrade_request_requested_at",
        table_name="role_upgrade_request",
    )
    op.drop_index(
        "ix_role_upgrade_request_status",
        table_name="role_upgrade_request",
    )
    op.drop_index(
        "ix_role_upgrade_request_user_id",
        table_name="role_upgrade_request",
    )
    op.drop_table("role_upgrade_request")
