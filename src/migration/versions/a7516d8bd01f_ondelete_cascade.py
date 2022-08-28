"""ondelete_CASCADE

Revision ID: a7516d8bd01f
Revises: 834dde41a769
Create Date: 2022-08-28 16:46:55.363097

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a7516d8bd01f'
down_revision = '834dde41a769'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint('customer_bill_user_id_fkey', 'customer_bill', type_='foreignkey')
    op.create_foreign_key(None, 'customer_bill', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('purchase_bill_id_fkey', 'purchase', type_='foreignkey')
    op.drop_constraint('purchase_product_id_fkey', 'purchase', type_='foreignkey')
    op.drop_constraint('purchase_user_id_fkey', 'purchase', type_='foreignkey')
    op.create_foreign_key(None, 'purchase', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'purchase', 'customer_bill', ['bill_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'purchase', 'product', ['product_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('transaction_user_id_fkey', 'transaction', type_='foreignkey')
    op.drop_constraint('transaction_bill_id_fkey', 'transaction', type_='foreignkey')
    op.create_foreign_key(None, 'transaction', 'user', ['user_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key(None, 'transaction', 'customer_bill', ['bill_id'], ['id'], ondelete='CASCADE')
