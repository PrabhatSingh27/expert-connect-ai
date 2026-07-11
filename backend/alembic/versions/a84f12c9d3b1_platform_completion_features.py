"""platform completion features

Revision ID: a84f12c9d3b1
Revises: 7d7ecb6b9a2d
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a84f12c9d3b1"
down_revision: Union[str, Sequence[str], None] = "7d7ecb6b9a2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _inspector():
    return sa.inspect(op.get_bind())


def _has_table(table_name: str) -> bool:
    return _inspector().has_table(table_name)


def _has_column(table_name: str, column_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(column["name"] == column_name for column in _inspector().get_columns(table_name))


def _has_index(table_name: str, index_name: str) -> bool:
    if not _has_table(table_name):
        return False
    return any(index["name"] == index_name for index in _inspector().get_indexes(table_name))


def upgrade() -> None:
    if not _has_column("users", "is_active"):
        op.add_column("users", sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False))

    expert_columns = {
        "government_id_file_url": sa.Column("government_id_file_url", sa.String(), nullable=True),
        "service_city": sa.Column("service_city", sa.String(), nullable=True),
        "service_pincodes": sa.Column("service_pincodes", sa.Text(), nullable=True),
        "profile_image_url": sa.Column("profile_image_url", sa.String(), nullable=True),
        "experience_years": sa.Column("experience_years", sa.Integer(), server_default="0", nullable=False),
        "is_verified": sa.Column("is_verified", sa.Boolean(), server_default="false", nullable=False),
        "is_active": sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    }
    for column_name, column in expert_columns.items():
        if not _has_column("experts", column_name):
            op.add_column("experts", column)

    issue_columns = {
        "problem_type": sa.Column("problem_type", sa.String(), nullable=True),
        "urgency": sa.Column("urgency", sa.String(), nullable=True),
        "required_skills": sa.Column("required_skills", sa.Text(), nullable=True),
        "confidence_score": sa.Column("confidence_score", sa.Float(), nullable=True),
        "ai_explanation": sa.Column("ai_explanation", sa.Text(), nullable=True),
    }
    for column_name, column in issue_columns.items():
        if not _has_column("issues", column_name):
            op.add_column("issues", column)

    if not _has_table("issue_attachments"):
        op.create_table(
            "issue_attachments",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("issue_id", sa.Integer(), nullable=False),
            sa.Column("file_url", sa.String(), nullable=False),
            sa.Column("file_type", sa.String(), nullable=False),
            sa.Column("original_filename", sa.String(), nullable=True),
            sa.Column("content_type", sa.String(), nullable=True),
            sa.Column("file_size", sa.Integer(), nullable=True),
            sa.Column("size_bytes", sa.Integer(), nullable=True),
            sa.Column("storage_provider", sa.String(), server_default="local", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["issue_id"], ["issues.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
    if not _has_index("issue_attachments", "ix_issue_attachments_id"):
        op.create_index(op.f("ix_issue_attachments_id"), "issue_attachments", ["id"], unique=False)
    if _has_table("issue_attachments") and not _has_column("issue_attachments", "file_size"):
        op.add_column("issue_attachments", sa.Column("file_size", sa.Integer(), nullable=True))

    if not _has_table("expert_reviews"):
        op.create_table(
            "expert_reviews",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("issue_id", sa.Integer(), nullable=False),
            sa.Column("expert_id", sa.Integer(), nullable=False),
            sa.Column("customer_id", sa.Integer(), nullable=False),
            sa.Column("rating", sa.Integer(), nullable=False),
            sa.Column("review", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["customer_id"], ["users.id"]),
            sa.ForeignKeyConstraint(["expert_id"], ["experts.id"]),
            sa.ForeignKeyConstraint(["issue_id"], ["issues.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("issue_id", "customer_id", name="uq_expert_review_issue_customer"),
        )
    if not _has_index("expert_reviews", "ix_expert_reviews_id"):
        op.create_index(op.f("ix_expert_reviews_id"), "expert_reviews", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_expert_reviews_id"), table_name="expert_reviews")
    op.drop_table("expert_reviews")
    op.drop_index(op.f("ix_issue_attachments_id"), table_name="issue_attachments")
    op.drop_table("issue_attachments")

    op.drop_column("issues", "ai_explanation")
    op.drop_column("issues", "confidence_score")
    op.drop_column("issues", "required_skills")
    op.drop_column("issues", "urgency")
    op.drop_column("issues", "problem_type")

    op.drop_column("experts", "is_active")
    op.drop_column("experts", "is_verified")
    op.drop_column("experts", "experience_years")
    op.drop_column("experts", "profile_image_url")
    op.drop_column("experts", "service_pincodes")
    op.drop_column("experts", "service_city")
    op.drop_column("experts", "government_id_file_url")

    op.drop_column("users", "is_active")
