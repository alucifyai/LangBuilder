"""merge rbac and main branches

Revision ID: 19db92f8586c
Revises: 3162e83e485f, d73ae349cf9c
Create Date: 2025-11-06 09:00:11.206934

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.engine.reflection import Inspector
from langbuilder.utils import migration


# revision identifiers, used by Alembic.
revision: str = '19db92f8586c'
down_revision: Union[str, None] = ('3162e83e485f', 'd73ae349cf9c')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    pass


def downgrade() -> None:
    conn = op.get_bind()
    pass
