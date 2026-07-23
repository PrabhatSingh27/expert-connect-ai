"""add operator suspension and admin override tracking

Revision ID: d4e9f2a8c1b7
Revises: b1c6e0d5f2a1
"""

from alembic import op
import sqlalchemy as sa


revision = "d4e9f2a8c1b7"
down_revision = "b1c6e0d5f2a1"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    return any(
        column["name"] == column_name
        for column in sa.inspect(op.get_bind()).get_columns(table_name)
    )


def upgrade() -> None:
    if not _has_column("users", "account_status"):
        op.add_column(
            "users",
            sa.Column("account_status", sa.String(), server_default="active", nullable=False),
        )
    if not _has_column("issues", "admin_override_at"):
        op.add_column("issues", sa.Column("admin_override_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    if _has_column("issues", "admin_override_at"):
        op.drop_column("issues", "admin_override_at")
    if _has_column("users", "account_status"):
        op.drop_column("users", "account_status")
