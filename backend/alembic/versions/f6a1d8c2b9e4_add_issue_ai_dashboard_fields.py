"""persist AI dashboard detected and response fields

Revision ID: f6a1d8c2b9e4
Revises: d4e9f2a8c1b7
"""

from alembic import op
import sqlalchemy as sa


revision = "f6a1d8c2b9e4"
down_revision = "d4e9f2a8c1b7"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    return any(
        column["name"] == column_name
        for column in sa.inspect(op.get_bind()).get_columns(table_name)
    )


def upgrade() -> None:
    if not _has_column("issues", "detected"):
        op.add_column("issues", sa.Column("detected", sa.Text(), nullable=True))
    if not _has_column("issues", "response"):
        op.add_column("issues", sa.Column("response", sa.Text(), nullable=True))
    op.execute("UPDATE issues SET detected = ai_explanation WHERE detected IS NULL AND ai_explanation IS NOT NULL")
    op.execute("UPDATE issues SET response = ai_explanation WHERE response IS NULL AND ai_explanation IS NOT NULL")


def downgrade() -> None:
    if _has_column("issues", "response"):
        op.drop_column("issues", "response")
    if _has_column("issues", "detected"):
        op.drop_column("issues", "detected")
