"""fix gps_track

Revision ID: a6cf1b1881f7
Revises: 4189dbb5a574
Create Date: 2026-04-08 21:24:26.003025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2


# revision identifiers, used by Alembic.
revision: str = 'a6cf1b1881f7'
down_revision: Union[str, Sequence[str], None] = '4189dbb5a574'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
    # ### end Alembic commands ###
