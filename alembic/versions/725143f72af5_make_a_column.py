"""make a column

Revision ID: 725143f72af5
Revises: d90ba147387f
Create Date: 2024-07-02 22:18:20.625404

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '725143f72af5'
down_revision: Union[str, None] = 'd90ba147387f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('account', sa.Column('last_transaction_date', sa.Datetime))


def downgrade() -> None:
    op.drop_column('account', 'last_transaction_date')
