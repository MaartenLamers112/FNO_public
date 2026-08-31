"""Voeg aantal personen voor ongenummerde weergave toe.

Revision ID: e6d9a4b73c21
Revises: c4a7e2d19b83
"""

import sqlalchemy as sa
from alembic import op

revision = "e6d9a4b73c21"
down_revision = "c4a7e2d19b83"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Voeg person_display_count toe aan photo."""

    with op.batch_alter_table("photo") as batch_op:
        batch_op.add_column(
            sa.Column(
                "person_display_count",
                sa.Integer(),
                nullable=False,
                server_default="1",
            )
        )


def downgrade() -> None:
    """Verwijder person_display_count uit photo."""

    with op.batch_alter_table("photo") as batch_op:
        batch_op.drop_column("person_display_count")
