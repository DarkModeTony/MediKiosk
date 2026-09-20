"""add encounter_id to doctalk_consultation_notes

Revision ID: e6f7a8b9c0d1
Revises: d5e82f1a9b3c
Create Date: 2026-09-20 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd5e82f1a9b3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_tables = insp.get_table_names()

    if 'doctalk_consultation_notes' in existing_tables:
        notes_cols = [c['name'] for c in insp.get_columns('doctalk_consultation_notes')]
        if 'encounter_id' not in notes_cols:
            op.add_column(
                'doctalk_consultation_notes',
                sa.Column('encounter_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('encounters.id'), nullable=True)
            )
        
        notes_indexes = [idx['name'] for idx in insp.get_indexes('doctalk_consultation_notes')]
        if 'ix_doctalk_consultation_notes_encounter_id' not in notes_indexes:
            op.create_index('ix_doctalk_consultation_notes_encounter_id', 'doctalk_consultation_notes', ['encounter_id'])


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    existing_tables = insp.get_table_names()

    if 'doctalk_consultation_notes' in existing_tables:
        notes_cols = [c['name'] for c in insp.get_columns('doctalk_consultation_notes')]
        if 'encounter_id' in notes_cols:
            op.drop_column('doctalk_consultation_notes', 'encounter_id')
