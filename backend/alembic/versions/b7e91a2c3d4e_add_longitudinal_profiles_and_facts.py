"""add longitudinal profiles and facts

Revision ID: b7e91a2c3d4e
Revises: 4f6c80f861c0
Create Date: 2026-09-15 11:42:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7e91a2c3d4e'
down_revision: Union[str, Sequence[str], None] = '4f6c80f861c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'patient_longitudinal_profiles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('schema_version', sa.String(), nullable=True, server_default='1.0'),
        sa.Column('profile', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_longitudinal_profiles_patient_id'), 'patient_longitudinal_profiles', ['patient_id'], unique=True)

    op.create_table(
        'patient_facts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('patient_id', sa.UUID(), nullable=False),
        sa.Column('encounter_id', sa.UUID(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('fact_type', sa.String(), nullable=True),
        sa.Column('body_site', sa.String(), nullable=True),
        sa.Column('laterality', sa.String(), nullable=True),
        sa.Column('value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=True, server_default='active'),
        sa.Column('source_type', sa.String(), nullable=True, server_default='patient_statement'),
        sa.Column('source_id', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=True, server_default='false'),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], ),
        sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_facts_patient_id'), 'patient_facts', ['patient_id'], unique=False)
    op.create_index(op.f('ix_patient_facts_category'), 'patient_facts', ['category'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_patient_facts_category'), table_name='patient_facts')
    op.drop_index(op.f('ix_patient_facts_patient_id'), table_name='patient_facts')
    op.drop_table('patient_facts')
    op.drop_index(op.f('ix_patient_longitudinal_profiles_patient_id'), table_name='patient_longitudinal_profiles')
    op.drop_table('patient_longitudinal_profiles')
