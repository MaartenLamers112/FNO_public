"""Voeg personenweergave per foto toe.

Revision ID: 9b5d6c1a42f0
Revises: 7b8d5f2a91c4
"""

import sqlalchemy as sa
from alembic import op

revision = "9b5d6c1a42f0"
down_revision = "7b8d5f2a91c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Voeg de personenweergave toe aan foto's."""

    with op.batch_alter_table("photo") as batch_op:
        batch_op.add_column(
            sa.Column(
                "person_display_mode",
                sa.String(length=20),
                nullable=False,
                server_default="numbered",
            )
        )


def downgrade() -> None:
    """Verwijder de personenweergave van foto's."""

    with op.batch_alter_table("photo") as batch_op:
        batch_op.drop_column("person_display_mode")
