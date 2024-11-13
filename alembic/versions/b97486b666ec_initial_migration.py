"""initial migration

Revision ID: b97486b666ec
Revises: 
Create Date: 2024-11-09 09:00:45.516497

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b97486b666ec"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "services",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("service_name", sa.String(length=255), nullable=False),
        sa.Column("owner_team", sa.String(length=255), nullable=False),
        sa.Column("repository_source", sa.Text(), nullable=False),
        sa.Column("lifecycle_status", sa.String(length=50), nullable=False),
        sa.Column("consolidation_confict", sa.Boolean(), nullable=True),
        sa.Column(
            "last_updated",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("services")
    # ### end Alembic commands ###