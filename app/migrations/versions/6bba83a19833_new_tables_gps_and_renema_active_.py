"""new tables gps and renema active_training_id to training_id

Revision ID: 6bba83a19833
Revises: 1d8df1413f23
Create Date: 2026-04-01 20:31:35.897101

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bba83a19833'
down_revision: Union[str, Sequence[str], None] = '1d8df1413f23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Сначала переименовываем столбец
    op.alter_column('completed_training', 'active_training_id',
                     new_column_name='training_id')
    
    # 2. Потом создаём таблицу с FK на уже переименованный столбец
    op.create_table('training_gps_points',
        sa.Column('gps_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('training_id', sa.UUID(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('altitude', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['training_id'], ['completed_training.training_id']),
        sa.PrimaryKeyConstraint('gps_id')
    )
    op.create_index(op.f('ix_training_gps_points_training_id'), 'training_gps_points', ['training_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_training_gps_points_training_id'), table_name='training_gps_points')
    op.drop_table('training_gps_points')
    op.alter_column('completed_training', 'training_id',
                     new_column_name='active_training_id')
