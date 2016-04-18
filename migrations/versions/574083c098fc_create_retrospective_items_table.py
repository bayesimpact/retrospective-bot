"""create retrospective_items table

Revision ID: 574083c098fc
Revises: 201bae6698f6
Create Date: 2016-04-18 14:56:01.271624

"""

# revision identifiers, used by Alembic.
revision = '574083c098fc'
down_revision = '201bae6698f6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table('sprints',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_name', sa.Unicode(), nullable=True),
        sa.Column('creation_date', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'))

    op.create_table('retrospective_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sprint_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.Unicode(), nullable=True),
        sa.Column('text', sa.Unicode(), nullable=True),
        sa.Column('user_name', sa.Unicode(), nullable=True),
        sa.Column('creation_date', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'))
    op.create_index(op.f('ix_retrospective_items'), 'retrospective_items', ['sprint_id', 'category'], unique=False)


def downgrade():
    op.drop_table('sprints')

    op.drop_index(op.f('ix_retrospective_items'), table_name='retrospective_items')
    op.drop_table('retrospective_items')
