"""add is_admin to user and time_limit to questions

Revision ID: ff_add_is_admin_and_time_limit
Revises: e96865e4fa62
Create Date: 2025-12-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ff_add_is_admin_and_time_limit'
down_revision = 'e96865e4fa62'
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()))
    with op.batch_alter_table('questions') as batch_op:
        batch_op.add_column(sa.Column('time_limit', sa.Integer(), nullable=False, server_default='60'))

    # Remove server defaults after migration to keep application-level defaults
    op.execute("""
        ALTER TABLE user ALTER COLUMN is_admin DROP DEFAULT
    """) if op.get_bind().dialect.name != 'sqlite' else None
    op.execute("""
        ALTER TABLE questions ALTER COLUMN time_limit DROP DEFAULT
    """) if op.get_bind().dialect.name != 'sqlite' else None

def downgrade():
    with op.batch_alter_table('questions') as batch_op:
        batch_op.drop_column('time_limit')
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('is_admin')
