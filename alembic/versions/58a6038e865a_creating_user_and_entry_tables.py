"""creating User and Entry tables

Revision ID: 58a6038e865a
Revises: 
Create Date: 2024-07-10 22:38:04.785737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '58a6038e865a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

emotionsenum = postgresql.ENUM(
    'SADNESS', 'HAPPINESS', 'FEAR', 'ANGER', 'SURPRISE', 'DISGUST', name='emotionsenum')


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('username', sa.String(), nullable=False),
                    sa.Column('created_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=False),
                    sa.Column('hashed_password', sa.String(), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('entries',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(),
                              server_default=sa.text('now()'), nullable=False),
                    sa.Column('date', sa.Date(), server_default=sa.text(
                        'now()'), nullable=False),
                    sa.Column('emotions', postgresql.ARRAY(
                        emotionsenum), nullable=False),
                    sa.Column('content', sa.Text(), nullable=False),
                    sa.Column('embeddings', postgresql.ARRAY(
                        sa.Float()), nullable=True),
                    sa.Column('author_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('entries')
    op.drop_table('users')
    # ### end Alembic commands ###
