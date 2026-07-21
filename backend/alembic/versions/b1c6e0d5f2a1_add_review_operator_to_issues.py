"""add review operator to issues

Revision ID: b1c6e0d5f2a1
Revises: a84f12c9d3b1
"""

from alembic import op
import sqlalchemy as sa


revision = "b1c6e0d5f2a1"
down_revision = "a84f12c9d3b1"
branch_labels = None
depends_on = None


def _has_column(table_name: str, column_name: str) -> bool:
    return any(
        column["name"] == column_name
        for column in sa.inspect(op.get_bind()).get_columns(table_name)
    )


def _has_foreign_key(table_name: str, column_name: str) -> bool:
    return any(
        foreign_key["constrained_columns"] == [column_name]
        and foreign_key["referred_table"] == "users"
        for foreign_key in sa.inspect(op.get_bind()).get_foreign_keys(table_name)
    )


def upgrade() -> None:
    if not _has_column("issues", "review_operator_id"):
        op.add_column("issues", sa.Column("review_operator_id", sa.Integer(), nullable=True))
    if not _has_foreign_key("issues", "review_operator_id"):
        op.create_foreign_key(
            "issues_review_operator_id_fkey",
            "issues",
            "users",
            ["review_operator_id"],
            ["id"],
        )
    op.create_index(
        "ix_issues_review_operator_id",
        "issues",
        ["review_operator_id"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index("ix_issues_review_operator_id", table_name="issues", if_exists=True)
    op.drop_constraint("issues_review_operator_id_fkey", "issues", type_="foreignkey", if_exists=True)
    op.drop_column("issues", "review_operator_id")
