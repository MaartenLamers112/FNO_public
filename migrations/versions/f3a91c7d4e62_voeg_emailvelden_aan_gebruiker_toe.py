"""Voeg e-mailvelden aan gebruikers toe.

Revision ID: f3a91c7d4e62
Revises: e6d9a4b73c21
"""

import sqlalchemy as sa
from alembic import op

revision = "f3a91c7d4e62"
down_revision = "e6d9a4b73c21"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Voeg e-mail en verificatiestatus toe aan user."""

    op.execute("DROP TABLE IF EXISTS _alembic_tmp_user")

    op.add_column(
        "user",
        sa.Column(
            "email",
            sa.String(length=320),
            nullable=True,
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_index(
        "ix_user_email",
        "user",
        ["email"],
        unique=True,
    )


def downgrade() -> None:
    """Verwijder e-mail en verificatiestatus uit user."""

    op.drop_index("ix_user_email", table_name="user")
    op.drop_column("user", "email_verified")
    op.drop_column("user", "email")
