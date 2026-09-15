"""add prescription workflow fields

Revision ID: c3f81e7d9a2b
Revises: b7e91a2c3d4e
Create Date: 2026-09-15 18:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3f81e7d9a2b'
down_revision: Union[str, Sequence[str], None] = 'b7e91a2c3d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to prescriptions
    op.add_column('prescriptions', sa.Column('patient_id', sa.UUID(), nullable=True))
    op.create_foreign_key('fk_prescriptions_patient_id', 'prescriptions', 'patients', ['patient_id'], ['id'])
    op.add_column('prescriptions', sa.Column('status', sa.String(), server_default='DRAFT', nullable=True))
    op.add_column('prescriptions', sa.Column('notes', sa.Text(), nullable=True))
    op.add_column('prescriptions', sa.Column('finalized_at', sa.DateTime(), nullable=True))
    op.add_column('prescriptions', sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Add columns to prescription_items
    op.add_column('prescription_items', sa.Column('medicine_id', sa.Integer(), nullable=True))
    op.add_column('prescription_items', sa.Column('generic_name', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('strength', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('dosage_form', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('dose', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('dose_unit', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('route', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('frequency', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('timing', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('duration_value', sa.Integer(), nullable=True))
    op.add_column('prescription_items', sa.Column('duration_unit', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('quantity', sa.Integer(), nullable=True))
    op.add_column('prescription_items', sa.Column('indication', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('is_prn', sa.Boolean(), server_default=sa.false(), nullable=True))
    op.add_column('prescription_items', sa.Column('min_interval', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('max_daily_dose', sa.String(), nullable=True))
    op.add_column('prescription_items', sa.Column('status', sa.String(), server_default='active', nullable=True))
    op.add_column('prescription_items', sa.Column('item_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('prescription_items', sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    # Drop prescription_items columns
    op.drop_column('prescription_items', 'created_at')
    op.drop_column('prescription_items', 'item_metadata')
    op.drop_column('prescription_items', 'status')
    op.drop_column('prescription_items', 'max_daily_dose')
    op.drop_column('prescription_items', 'min_interval')
    op.drop_column('prescription_items', 'is_prn')
    op.drop_column('prescription_items', 'indication')
    op.drop_column('prescription_items', 'quantity')
    op.drop_column('prescription_items', 'duration_unit')
    op.drop_column('prescription_items', 'duration_value')
    op.drop_column('prescription_items', 'timing')
    op.drop_column('prescription_items', 'frequency')
    op.drop_column('prescription_items', 'route')
    op.drop_column('prescription_items', 'dose_unit')
    op.drop_column('prescription_items', 'dose')
    op.drop_column('prescription_items', 'dosage_form')
    op.drop_column('prescription_items', 'strength')
    op.drop_column('prescription_items', 'generic_name')
    op.drop_column('prescription_items', 'medicine_id')

    # Drop prescriptions columns
    op.drop_constraint('fk_prescriptions_patient_id', 'prescriptions', type_='foreignkey')
    op.drop_column('prescriptions', 'updated_at')
    op.drop_column('prescriptions', 'finalized_at')
    op.drop_column('prescriptions', 'notes')
    op.drop_column('prescriptions', 'status')
    op.drop_column('prescriptions', 'patient_id')
