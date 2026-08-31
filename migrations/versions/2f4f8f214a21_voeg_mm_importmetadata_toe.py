"""Voeg MM-importmetadata toe.

Revision ID: 2f4f8f214a21
Revises: dde44c75a09e
"""

import sqlalchemy as sa
from alembic import op

revision = "2f4f8f214a21"
down_revision = "dde44c75a09e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Voeg metadata-snapshot en importopdrachten toe."""

    with op.batch_alter_table("photo") as batch_op:
        batch_op.add_column(sa.Column("mm_metadata", sa.JSON(), nullable=True))

    op.create_table(
        "mm_import_job",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("found_count", sa.Integer(), nullable=False),
        sa.Column("imported_count", sa.Integer(), nullable=False),
        sa.Column("skipped_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mm_import_job_user_id", "mm_import_job", ["user_id"])


def downgrade() -> None:
    """Verwijder metadata-snapshot en importopdrachten."""

    op.drop_index("ix_mm_import_job_user_id", table_name="mm_import_job")
    op.drop_table("mm_import_job")
    with op.batch_alter_table("photo") as batch_op:
        batch_op.drop_column("mm_metadata")
