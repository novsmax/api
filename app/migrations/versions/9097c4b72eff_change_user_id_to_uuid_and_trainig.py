"""change user_id to uuid and trainig

Revision ID: 9097c4b72eff
Revises: 6bba83a19833
Create Date: 2026-04-02 10:36:19.627862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9097c4b72eff'
down_revision: Union[str, Sequence[str], None] = '6bba83a19833'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('training_gps_points')  # ← добавить первой
    op.drop_table('user_and_goal')
    op.drop_table('user_and_role')
    op.drop_table('trainers')
    op.drop_table('club_organizer')
    op.drop_table('email_verifications')
    op.drop_table('completed_training')
    op.drop_table('users')
    # ... остальное без изменений

    # Пересоздаём с UUID
    op.create_table('users',
        sa.Column('user_id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('middle_name', sa.String(100), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('gender', sa.String(10), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('nickname', sa.String(100), nullable=False, unique=True),
        sa.Column('jwt_session', sa.String(500), nullable=True),
        sa.Column('jwt_reload', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token_hash', sa.String(255), nullable=True),
        sa.Column('password_reset_token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('user_id')
    )

    op.create_table('email_verifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('code', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=True, default=0),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('user_and_goal',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('goal_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['goal_id'], ['goal_register.goal_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'goal_id')
    )

    op.create_table('user_and_role',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    op.create_table('trainers',
        sa.Column('trainer_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('trainer_id')
    )

    op.create_table('club_organizer',
        sa.Column('club_organizer_id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('club_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['club_id'], ['clubs.club_id']),
        sa.ForeignKeyConstraint(['role_id'], ['roles.role_id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('club_organizer_id')
    )

    op.create_table('completed_training',
        sa.Column('training_id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('type_activ_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('time_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('time_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('data_training', sa.Text(), nullable=True),
        sa.Column('kilocalories', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('training_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('user_and_role', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('user_and_goal', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('trainers', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.drop_constraint(None, 'completed_training', type_='foreignkey')
    op.alter_column('completed_training', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    op.alter_column('club_organizer', 'user_id',
               existing_type=sa.UUID(),
               type_=sa.INTEGER(),
               existing_nullable=False)
    # ### end Alembic commands ###
