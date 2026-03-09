"""artifact link to ticket

Revision ID: a3f1c2b4d5e6
Revises: 5d2d67a9de8c
Create Date: 2026-03-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a3f1c2b4d5e6'
down_revision = '5d2d67a9de8c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. 加 ticket_id 列（先允许 NULL，填完存量数据再改成 NOT NULL）
    op.add_column('artifacts', sa.Column('ticket_id', sa.Integer(), nullable=True))

    # 2. 存量数据：从 run 反查 ticket_id 填上
    op.execute("""
        UPDATE artifacts
        SET ticket_id = runs.ticket_id
        FROM runs
        WHERE artifacts.run_id = runs.id
    """)

    # 3. 改成 NOT NULL
    op.alter_column('artifacts', 'ticket_id', nullable=False)

    # 4. 加外键
    op.create_foreign_key(
        'fk_artifacts_ticket_id',
        'artifacts', 'tickets',
        ['ticket_id'], ['id']
    )

    # 5. run_id 改成可选
    op.alter_column('artifacts', 'run_id', nullable=True)


def downgrade() -> None:
    op.alter_column('artifacts', 'run_id', nullable=False)
    op.drop_constraint('fk_artifacts_ticket_id', 'artifacts', type_='foreignkey')
    op.drop_column('artifacts', 'ticket_id')
