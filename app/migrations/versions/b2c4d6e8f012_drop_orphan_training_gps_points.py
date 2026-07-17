"""drop orphan training_gps_points

Таблица training_gps_points должна была быть удалена ещё миграцией
4189dbb5a574 ("add gps_track to completed_training and drop training_gps_points"),
но op.drop_table там был потерян, и таблица осталась в схеме. Приложение её
не использует: GPS-точки хранятся в Cassandra (gps_points), а трек — в
completed_training.gps_track. Доводим удаление до конца.

Revision ID: b2c4d6e8f012
Revises: 9a3f1b7c2d84
Create Date: 2026-07-17 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b2c4d6e8f012'
down_revision: Union[str, Sequence[str], None] = '9a3f1b7c2d84'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Удалить осиротевшую таблицу training_gps_points."""
    op.drop_index(op.f('ix_training_gps_points_training_id'), table_name='training_gps_points')
    op.drop_table('training_gps_points')


def downgrade() -> None:
    """Воссоздать структуру training_gps_points (без данных)."""
    op.create_table(
        'training_gps_points',
        sa.Column('gps_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('training_id', sa.UUID(), nullable=False),
        sa.Column('recorded_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('altitude', sa.Float(), nullable=True),
        sa.Column('speed', sa.Float(), nullable=True),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['training_id'], ['completed_training.training_id'], ),
        sa.PrimaryKeyConstraint('gps_id'),
    )
    op.create_index(
        op.f('ix_training_gps_points_training_id'),
        'training_gps_points', ['training_id'], unique=False,
    )
