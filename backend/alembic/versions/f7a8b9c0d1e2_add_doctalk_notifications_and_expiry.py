"""add doctalk notifications and expiry
 
Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-09-20 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f7a8b9c0d1e2'
down_revision: Union[str, Sequence[str], None] = 'e6f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_tables = insp.get_table_names()

    # 1. Add expires_at column to doctalk_consultations if missing
    if 'doctalk_consultations' in existing_tables:
        consult_cols = [c['name'] for c in insp.get_columns('doctalk_consultations')]
        if 'expires_at' not in consult_cols:
            op.add_column(
                'doctalk_consultations',
                sa.Column('expires_at', sa.DateTime(), nullable=True)
            )
        consult_indexes = [idx['name'] for idx in insp.get_indexes('doctalk_consultations')]
        if 'ix_doctalk_consultations_expires_at' not in consult_indexes:
            op.create_index('ix_doctalk_consultations_expires_at', 'doctalk_consultations', ['expires_at'])

    # 2. Create doctalk_notifications table if missing
    if 'doctalk_notifications' not in existing_tables:
        op.create_table(
            'doctalk_notifications',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('consultation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('doctalk_consultations.id'), nullable=True),
            sa.Column('encounter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('encounters.id'), nullable=True),
            sa.Column('event_type', sa.String(), nullable=False),
            sa.Column('title', sa.String(), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('severity', sa.String(), server_default='INFO', nullable=True),
            sa.Column('is_read', sa.Boolean(), server_default=sa.false(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        )
        op.create_index('ix_doctalk_notifications_user_id', 'doctalk_notifications', ['user_id'])
        op.create_index('ix_doctalk_notifications_consultation_id', 'doctalk_notifications', ['consultation_id'])
        op.create_index('ix_doctalk_notifications_encounter_id', 'doctalk_notifications', ['encounter_id'])
        op.create_index('ix_doctalk_notifications_event_type', 'doctalk_notifications', ['event_type'])
        op.create_index('ix_doctalk_notifications_is_read', 'doctalk_notifications', ['is_read'])
        op.create_index('ix_doctalk_notifications_created_at', 'doctalk_notifications', ['created_at'])


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_tables = insp.get_table_names()

    if 'doctalk_notifications' in existing_tables:
        op.drop_table('doctalk_notifications')

    if 'doctalk_consultations' in existing_tables:
        consult_cols = [c['name'] for c in insp.get_columns('doctalk_consultations')]
        if 'expires_at' in consult_cols:
            op.drop_column('doctalk_consultations', 'expires_at')
