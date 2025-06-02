"""merge heads

Revision ID: a4453902f3c0
Revises: 9db22a996d6e, a3711cfde0df
Create Date: 2025-05-26 10:54:38.168910

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a4453902f3c0'
down_revision: Union[str, None] = ('9db22a996d6e', 'a3711cfde0df')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
