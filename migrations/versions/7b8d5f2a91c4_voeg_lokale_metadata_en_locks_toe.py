"""Voeg lokale metadata, zichtbaarheid en naamlocks toe.

Revision ID: 7b8d5f2a91c4
Revises: 2f4f8f214a21
"""

import sqlalchemy as sa
from alembic import op

revision = "7b8d5f2a91c4"
down_revision = "2f4f8f214a21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Voeg de velden voor blok 3.6 toe."""

    with op.batch_alter_table("photo") as batch_op:
        batch_op.add_column(sa.Column("local_subject", sa.String(250), nullable=True))
        batch_op.add_column(sa.Column("local_date", sa.String(100), nullable=True))
        batch_op.add_column(sa.Column("local_location", sa.String(250), nullable=True))
        batch_op.add_column(sa.Column("local_description", sa.Text(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_visible", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )
        batch_op.add_column(
            sa.Column(
                "is_complete", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )
        batch_op.create_index("ix_photo_is_visible", ["is_visible"])
        batch_op.create_index("ix_photo_is_complete", ["is_complete"])
    op.execute("UPDATE photo SET is_visible = 1 WHERE publication_status = 1")
    with op.batch_alter_table("person") as batch_op:
        batch_op.add_column(
            sa.Column(
                "name_locked", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )


def downgrade() -> None:
    """Verwijder de velden voor blok 3.6."""

    with op.batch_alter_table("person") as batch_op:
        batch_op.drop_column("name_locked")
    with op.batch_alter_table("photo") as batch_op:
        batch_op.drop_index("ix_photo_is_complete")
        batch_op.drop_index("ix_photo_is_visible")
        batch_op.drop_column("is_complete")
        batch_op.drop_column("is_visible")
        batch_op.drop_column("local_description")
        batch_op.drop_column("local_location")
        batch_op.drop_column("local_date")
        batch_op.drop_column("local_subject")
