"""remove bookings table

Revision ID: 0c1b7422846c
Revises: c9b8679d3bc8
Create Date: 2026-07-01 10:46:40.748248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c1b7422846c'
down_revision: Union[str, Sequence[str], None] = 'c9b8679d3bc8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
