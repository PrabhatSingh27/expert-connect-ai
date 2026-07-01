"""remove bookings table

Revision ID: c9b8679d3bc8
Revises: 9c6c6bdaaeac
Create Date: 2026-07-01 10:40:46.303399

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9b8679d3bc8'
down_revision: Union[str, Sequence[str], None] = '9c6c6bdaaeac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table("bookings")


def downgrade() -> None:
    op.create_table(
        "bookings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expert_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("booking_date", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
    )