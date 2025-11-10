"""Add local_image_path to InvoiceRequest

Revision ID: $(uuidgen | tr '[:upper:]' '[:lower:]' | cut -d'-' -f1)
Revises: d2acb7d61f1c
Create Date: 2025-11-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'local_img_path_001'
down_revision = 'd2acb7d61f1c'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('invoice_requests', schema=None) as batch_op:
        batch_op.add_column(sa.Column('local_image_path', sa.String(length=512), nullable=True))


def downgrade():
    with op.batch_alter_table('invoice_requests', schema=None) as batch_op:
        batch_op.drop_column('local_image_path')
