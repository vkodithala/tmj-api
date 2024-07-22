"""making embedding column have 1024 vec

Revision ID: 6699d6ebbf85
Revises: 380a51946cd7
Create Date: 2024-07-20 23:04:55.717635

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector.sqlalchemy


# revision identifiers, used by Alembic.
revision: str = '6699d6ebbf85'
down_revision: Union[str, None] = '380a51946cd7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('entries', 'embedding',
                    existing_type=pgvector.sqlalchemy.Vector(dim=1536),
                    type_=pgvector.sqlalchemy.Vector(dim=1024),
                    existing_nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('entries', 'embedding',
                    existing_type=pgvector.sqlalchemy.Vector(dim=1024),
                    type_=pgvector.sqlalchemy.Vector(dim=1536),
                    existing_nullable=True)
    # ### end Alembic commands ###
