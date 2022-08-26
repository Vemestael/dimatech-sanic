"""initial

Revision ID: 7cd96b08822e
Revises: 
Create Date: 2022-08-24 21:06:57.215095

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7cd96b08822e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('User',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=150), nullable=False),
    sa.Column('password_hash', sa.LargeBinary(), nullable=False),
    sa.Column('salt', sa.LargeBinary(), nullable=False),
    sa.Column('email', sa.String(length=150), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_admin', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
