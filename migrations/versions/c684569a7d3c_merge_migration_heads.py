"""Merge migration heads

Revision ID: c684569a7d3c
Revises: local_img_path_001, e8f2a9b4c7d1
Create Date: 2025-11-14 20:12:10.271210

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c684569a7d3c'
down_revision = ('local_img_path_001', 'e8f2a9b4c7d1')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
