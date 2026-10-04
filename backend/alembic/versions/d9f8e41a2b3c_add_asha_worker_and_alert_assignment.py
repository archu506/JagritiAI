"""add asha worker and alert assignment

Revision ID: d9f8e41a2b3c
Revises: 753f7edff676
Create Date: 2026-08-15 11:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
import app.db.types


# revision identifiers, used by Alembic.
revision = 'd9f8e41a2b3c'
down_revision = '753f7edff676'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    if conn.dialect.name == 'postgresql':
        res = conn.execute(
            sa.text(
                "SELECT 1 FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
                "WHERE pg_type.typname = 'userrole' AND enumlabel = 'asha_worker'"
            )
        )
        if not res.scalar():
            with op.get_context().autocommit_block():
                op.execute(sa.text("ALTER TYPE userrole ADD VALUE 'asha_worker'"))

    op.add_column('alerts', sa.Column('assigned_asha_id', app.db.types.GUID(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('alerts', sa.Column('assigned_by', app.db.types.GUID(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('alerts', sa.Column('assigned_at', sa.DateTime(), nullable=True))
    op.add_column('alerts', sa.Column('verification_status', sa.String(length=20), server_default='pending', nullable=True))
    op.add_column('alerts', sa.Column('field_observation', sa.Text(), nullable=True))
    op.add_column('alerts', sa.Column('verified_at', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_alerts_assigned_asha_id'), 'alerts', ['assigned_asha_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_alerts_assigned_asha_id'), table_name='alerts')
    op.drop_column('alerts', 'verified_at')
    op.drop_column('alerts', 'field_observation')
    op.drop_column('alerts', 'verification_status')
    op.drop_column('alerts', 'assigned_at')
    op.drop_column('alerts', 'assigned_by')
    op.drop_column('alerts', 'assigned_asha_id')
