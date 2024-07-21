"""making embedding column non-nullable and having it use pgvector

Revision ID: 380a51946cd7
Revises: 76338180db2d
Create Date: 2024-07-20 22:39:39.211878

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector.sqlalchemy

# revision identifiers, used by Alembic.
revision: str = '380a51946cd7'
down_revision: Union[str, None] = '76338180db2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('entries', sa.Column(
        'embedding', pgvector.sqlalchemy.vector.VECTOR(dim=1536), nullable=True))
    op.drop_column('entries', 'embeddings')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('entries', sa.Column('embeddings', postgresql.ARRAY(
        sa.DOUBLE_PRECISION(precision=53)), autoincrement=False, nullable=True))
    op.drop_column('entries', 'embedding')
    # ### end Alembic commands ###
