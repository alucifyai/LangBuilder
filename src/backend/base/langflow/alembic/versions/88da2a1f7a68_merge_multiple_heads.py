"""merge multiple heads

Revision ID: 88da2a1f7a68
Revises: 0b4b33664011, 3162e83e485f
Create Date: 2025-10-11 22:20:31.344113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.engine.reflection import Inspector
from langflow.utils import migration


# revision identifiers, used by Alembic.
revision: str = '88da2a1f7a68'
down_revision: Union[str, None] = ('0b4b33664011', '3162e83e485f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    pass


def downgrade() -> None:
    conn = op.get_bind()
    pass
