"""Voeg labelgrootte per foto toe.

Revision ID: c4a7e2d19b83
Revises: 9b5d6c1a42f0
"""

import sqlalchemy as sa
from alembic import op

revision = "c4a7e2d19b83"
down_revision = "9b5d6c1a42f0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Voeg de labelgrootte toe aan foto's."""

    with op.batch_alter_table("photo") as batch_op:
        batch_op.add_column(
            sa.Column(
                "label_size",
                sa.Integer(),
                nullable=False,
                server_default="14",
            )
        )


def downgrade() -> None:
    """Verwijder de labelgrootte van foto's."""

    with op.batch_alter_table("photo") as batch_op:
        batch_op.drop_column("label_size")
