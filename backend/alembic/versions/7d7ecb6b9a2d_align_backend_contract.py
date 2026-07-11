"""align backend contract

Revision ID: 7d7ecb6b9a2d
Revises: ce8ed52fdc6d
Create Date: 2026-07-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7d7ecb6b9a2d"
down_revision: Union[str, Sequence[str], None] = "ce8ed52fdc6d"
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


def _drop_fk_for_column(table_name: str, column_name: str) -> None:
    if not _has_table(table_name):
        return

    for fk in _inspector().get_foreign_keys(table_name):
        if column_name in fk.get("constrained_columns", []):
            op.drop_constraint(fk["name"], table_name, type_="foreignkey")


def _has_fk_for_column(table_name: str, column_name: str, referred_table: str) -> bool:
    if not _has_table(table_name):
        return False

    for fk in _inspector().get_foreign_keys(table_name):
        if (
            column_name in fk.get("constrained_columns", [])
            and fk.get("referred_table") == referred_table
        ):
            return True
    return False


def upgrade() -> None:
    if not _has_column("users", "created_at"):
        op.add_column(
            "users",
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    op.alter_column("users", "role", server_default="customer", existing_type=sa.String(), nullable=False)

    if not _has_table("experts"):
        op.create_table(
            "experts",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("full_name", sa.String(), nullable=False),
            sa.Column("email", sa.String(), nullable=False),
            sa.Column("phone", sa.String(), nullable=False),
            sa.Column("government_id", sa.String(), nullable=False),
            sa.Column("skills", sa.Text(), nullable=False),
            sa.Column("service_area", sa.String(), nullable=False),
            sa.Column("bio", sa.Text(), nullable=True),
            sa.Column("permanent_address", sa.Text(), nullable=False),
            sa.Column("password_hash", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("email"),
            sa.UniqueConstraint("phone"),
        )
    if not _has_index("experts", "ix_experts_email"):
        op.create_index(op.f("ix_experts_email"), "experts", ["email"], unique=False)
    if not _has_index("experts", "ix_experts_id"):
        op.create_index(op.f("ix_experts_id"), "experts", ["id"], unique=False)

    if _has_table("availabilities"):
        op.execute("DELETE FROM availabilities")
        _drop_fk_for_column("availabilities", "user_id")
        if _has_column("availabilities", "user_id") and not _has_column("availabilities", "expert_id"):
            op.alter_column("availabilities", "user_id", new_column_name="expert_id", existing_type=sa.Integer(), nullable=False)
        elif _has_column("availabilities", "user_id") and _has_column("availabilities", "expert_id"):
            op.drop_column("availabilities", "user_id")
        if _has_column("availabilities", "expert_id"):
            op.alter_column("availabilities", "expert_id", existing_type=sa.Integer(), nullable=False)
            if not _has_fk_for_column("availabilities", "expert_id", "experts"):
                op.create_foreign_key(
                    "availabilities_expert_id_fkey",
                    "availabilities",
                    "experts",
                    ["expert_id"],
                    ["id"],
                )

    op.execute("UPDATE issues SET assigned_expert_id = NULL")
    _drop_fk_for_column("issues", "assigned_expert_id")
    if _has_column("issues", "assigned_expert_id") and not _has_fk_for_column("issues", "assigned_expert_id", "experts"):
        op.create_foreign_key(
            "issues_assigned_expert_id_fkey",
            "issues",
            "experts",
            ["assigned_expert_id"],
            ["id"],
        )
    op.alter_column("issues", "category", existing_type=sa.String(), nullable=True)
    op.alter_column("issues", "status", existing_type=sa.String(), nullable=False, server_default="open")
    if _has_column("issues", "preferred_visit_date"):
        op.execute(
            "ALTER TABLE issues ALTER COLUMN preferred_visit_date "
            "TYPE DATE USING NULLIF(preferred_visit_date::text, '')::date"
        )
    if not _has_column("issues", "image_path"):
        op.add_column("issues", sa.Column("image_path", sa.String(), nullable=True))
    if not _has_column("issues", "video_path"):
        op.add_column("issues", sa.Column("video_path", sa.String(), nullable=True))
    if not _has_column("issues", "audio_path"):
        op.add_column("issues", sa.Column("audio_path", sa.String(), nullable=True))
    if not _has_column("issues", "created_at"):
        op.add_column("issues", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))
    if not _has_column("issues", "updated_at"):
        op.add_column("issues", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

    if _has_table("expert_profiles"):
        if _has_index("expert_profiles", "ix_expert_profiles_id"):
            op.drop_index(op.f("ix_expert_profiles_id"), table_name="expert_profiles")
        op.drop_table("expert_profiles")


def downgrade() -> None:
    op.create_table(
        "expert_profiles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("skills", sa.Text(), nullable=True),
        sa.Column("experience_years", sa.Integer(), nullable=True),
        sa.Column("hourly_rate", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_expert_profiles_id"), "expert_profiles", ["id"], unique=False)

    op.drop_column("issues", "updated_at")
    op.drop_column("issues", "created_at")
    op.drop_column("issues", "audio_path")
    op.drop_column("issues", "video_path")
    op.drop_column("issues", "image_path")
    op.alter_column(
        "issues",
        "preferred_visit_date",
        type_=sa.String(),
        existing_type=sa.Date(),
        nullable=True,
    )
    op.alter_column("issues", "status", existing_type=sa.String(), nullable=True, server_default=None)
    op.drop_constraint("issues_assigned_expert_id_fkey", "issues", type_="foreignkey")
    op.create_foreign_key(
        "issues_assigned_expert_id_fkey",
        "issues",
        "users",
        ["assigned_expert_id"],
        ["id"],
    )

    op.drop_constraint("availabilities_expert_id_fkey", "availabilities", type_="foreignkey")
    op.alter_column("availabilities", "expert_id", new_column_name="user_id", existing_type=sa.Integer(), nullable=True)
    op.create_foreign_key(
        "availabilities_user_id_fkey",
        "availabilities",
        "users",
        ["user_id"],
        ["id"],
    )

    op.drop_index(op.f("ix_experts_id"), table_name="experts")
    op.drop_index(op.f("ix_experts_email"), table_name="experts")
    op.drop_table("experts")

    op.alter_column("users", "role", server_default=None, existing_type=sa.String(), nullable=False)
    op.drop_column("users", "created_at")
