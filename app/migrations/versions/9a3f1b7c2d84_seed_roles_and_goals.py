"""seed roles and goals

Revision ID: 9a3f1b7c2d84
Revises: f6465c2026cc
Create Date: 2026-07-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

from app.seeds.roles import seed_roles_and_goals, unseed_roles_and_goals

# revision identifiers, used by Alembic.
revision: str = '9a3f1b7c2d84'
down_revision: Union[str, Sequence[str], None] = 'f6465c2026cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Заполнить справочники ролей и целей регистрации шаблонными данными."""
    seed_roles_and_goals(op.get_bind())


def downgrade() -> None:
    """Убрать шаблонные роли и цели."""
    unseed_roles_and_goals(op.get_bind())
