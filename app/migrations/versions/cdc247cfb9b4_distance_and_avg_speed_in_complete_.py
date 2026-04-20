"""distance and avg speed in complete trainig

Revision ID: cdc247cfb9b4
Revises: dd9e5d903073
Create Date: 2026-04-20 18:45:02.572972

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cdc247cfb9b4'
down_revision: Union[str, Sequence[str], None] = 'dd9e5d903073'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('completed_training', sa.Column('distance_m', sa.Float(), nullable=True))
    op.add_column('completed_training', sa.Column('avg_speed', sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column('completed_training', 'avg_speed')
    op.drop_column('completed_training', 'distance_m')
