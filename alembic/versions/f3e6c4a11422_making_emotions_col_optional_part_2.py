"""making emotions col optional, part 2

Revision ID: f3e6c4a11422
Revises: f6f7bbc49346
Create Date: 2024-07-11 08:40:23.816128

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f3e6c4a11422'
down_revision: Union[str, None] = 'f6f7bbc49346'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('entries', 'emotions',
               existing_type=postgresql.ARRAY(postgresql.ENUM('SADNESS', 'HAPPINESS', 'FEAR', 'ANGER', 'SURPRISE', 'DISGUST', name='emotionsenum')),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('entries', 'emotions',
               existing_type=postgresql.ARRAY(postgresql.ENUM('SADNESS', 'HAPPINESS', 'FEAR', 'ANGER', 'SURPRISE', 'DISGUST', name='emotionsenum')),
               nullable=False)
    # ### end Alembic commands ###
