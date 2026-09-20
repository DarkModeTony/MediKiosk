"""add doctalk foundation

Revision ID: d5e82f1a9b3c
Revises: c3f81e7d9a2b
Create Date: 2026-09-20 03:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd5e82f1a9b3c'
down_revision: Union[str, Sequence[str], None] = 'c3f81e7d9a2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_tables = insp.get_table_names()
    user_cols = [c['name'] for c in insp.get_columns('users')] if 'users' in existing_tables else []

    # 1. Add columns to users table
    if 'display_name' not in user_cols:
        op.add_column('users', sa.Column('display_name', sa.String(), nullable=True))
    if 'specialty' not in user_cols:
        op.add_column('users', sa.Column('specialty', sa.String(), nullable=True))
    if 'sub_specialty' not in user_cols:
        op.add_column('users', sa.Column('sub_specialty', sa.String(), nullable=True))
    if 'qualification' not in user_cols:
        op.add_column('users', sa.Column('qualification', sa.String(), nullable=True))
    if 'doctalk_enabled' not in user_cols:
        op.add_column('users', sa.Column('doctalk_enabled', sa.Boolean(), server_default=sa.true(), nullable=True))
    if 'availability_status' not in user_cols:
        op.add_column('users', sa.Column('availability_status', sa.String(), server_default='AVAILABLE', nullable=True))
    if 'is_verified' not in user_cols:
        op.add_column('users', sa.Column('is_verified', sa.Boolean(), server_default=sa.true(), nullable=True))

    user_indexes = [idx['name'] for idx in insp.get_indexes('users')] if 'users' in existing_tables else []
    if 'ix_users_specialty' not in user_indexes:
        op.create_index('ix_users_specialty', 'users', ['specialty'])

    # 2. Create doctalk_consultations table
    if 'doctalk_consultations' not in existing_tables:
        op.create_table(
            'doctalk_consultations',
            sa.Column('id', sa.UUID(), primary_key=True),
            sa.Column('requesting_doctor_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('requesting_hospital_id', sa.UUID(), sa.ForeignKey('hospitals.id'), nullable=False),
            sa.Column('specialist_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('specialist_hospital_id', sa.UUID(), sa.ForeignKey('hospitals.id'), nullable=True),
            sa.Column('patient_id', sa.UUID(), sa.ForeignKey('patients.id'), nullable=False),
            sa.Column('patient_home_hospital_id', sa.UUID(), sa.ForeignKey('hospitals.id'), nullable=False),
            sa.Column('encounter_id', sa.UUID(), sa.ForeignKey('encounters.id'), nullable=False),
            sa.Column('specialty', sa.String(), nullable=False),
            sa.Column('reason', sa.Text(), nullable=False),
            sa.Column('urgency', sa.String(), server_default='ROUTINE', nullable=False),
            sa.Column('requested_duration_minutes', sa.Integer(), server_default='5', nullable=False),
            sa.Column('status', sa.String(), server_default='REQUESTED', nullable=False),
            sa.Column('access_scope', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('access_expires_at', sa.DateTime(), nullable=True),
            sa.Column('decline_reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('accepted_at', sa.DateTime(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        )

    consult_indexes = [idx['name'] for idx in insp.get_indexes('doctalk_consultations')] if 'doctalk_consultations' in existing_tables else []
    for idx_name, cols in [
        ('ix_doctalk_consultations_requesting_doctor_id', ['requesting_doctor_id']),
        ('ix_doctalk_consultations_specialist_id', ['specialist_id']),
        ('ix_doctalk_consultations_patient_id', ['patient_id']),
        ('ix_doctalk_consultations_encounter_id', ['encounter_id']),
        ('ix_doctalk_consultations_requesting_hospital_id', ['requesting_hospital_id']),
        ('ix_doctalk_consultations_specialist_hospital_id', ['specialist_hospital_id']),
        ('ix_doctalk_consultations_status', ['status']),
        ('ix_doctalk_consultations_created_at', ['created_at']),
    ]:
        if idx_name not in consult_indexes:
            op.create_index(idx_name, 'doctalk_consultations', cols)

    # 3. Create doctalk_consultation_notes table
    if 'doctalk_consultation_notes' not in existing_tables:
        op.create_table(
            'doctalk_consultation_notes',
            sa.Column('id', sa.UUID(), primary_key=True),
            sa.Column('consultation_id', sa.UUID(), sa.ForeignKey('doctalk_consultations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('specialist_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('specialist_hospital_id', sa.UUID(), sa.ForeignKey('hospitals.id'), nullable=False),
            sa.Column('clinical_opinion', sa.Text(), nullable=False),
            sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('further_evaluation', sa.Text(), nullable=True),
            sa.Column('follow_up', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
        )

    notes_indexes = [idx['name'] for idx in insp.get_indexes('doctalk_consultation_notes')] if 'doctalk_consultation_notes' in existing_tables else []
    if 'ix_doctalk_consultation_notes_consultation_id' not in notes_indexes:
        op.create_index('ix_doctalk_consultation_notes_consultation_id', 'doctalk_consultation_notes', ['consultation_id'])


def downgrade() -> None:
    op.drop_table('doctalk_consultation_notes')
    op.drop_table('doctalk_consultations')
    op.drop_index('ix_users_specialty', 'users')
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'availability_status')
    op.drop_column('users', 'doctalk_enabled')
    op.drop_column('users', 'qualification')
    op.drop_column('users', 'sub_specialty')
    op.drop_column('users', 'specialty')
    op.drop_column('users', 'display_name')
