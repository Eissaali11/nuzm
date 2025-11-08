"""Add speed_kmh and vehicle_id to employee_locations

Revision ID: e8f2a9b4c7d1
Revises: 5b2255ca9383
Create Date: 2025-11-08 13:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8f2a9b4c7d1'
down_revision = '5b2255ca9383'
branch_labels = None
depends_on = None


def upgrade():
    """Add speed_kmh and vehicle_id columns to employee_locations table"""
    with op.batch_alter_table('employee_locations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('speed_kmh', sa.Numeric(precision=6, scale=2), nullable=True))
        batch_op.add_column(sa.Column('vehicle_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_employee_locations_vehicle_id', 'vehicle', ['vehicle_id'], ['id'], ondelete='SET NULL')


def downgrade():
    """Remove speed_kmh and vehicle_id columns from employee_locations table"""
    with op.batch_alter_table('employee_locations', schema=None) as batch_op:
        batch_op.drop_constraint('fk_employee_locations_vehicle_id', type_='foreignkey')
        batch_op.drop_column('vehicle_id')
        batch_op.drop_column('speed_kmh')
