"""create pipeline components

Revision ID: 02955cc15633
Revises: 4fd38e9fefb3
Create Date: 2025-04-22 17:34:40.906049

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "02955cc15633"
down_revision: Union[str, None] = "4fd38e9fefb3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "component",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("input_path", sa.String, nullable=False),
        sa.Column("output_path", sa.String, nullable=False),
    )
    op.create_table(
        "pipeline",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("pipeline_components", sa.JSON, nullable=False),
        sa.Column("input_path", sa.String, nullable=False),
        sa.Column("output_path", sa.String, nullable=False),
    )
    op.create_table(
        "pipeline_component",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("description", sa.String, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("pipeline_component")
    op.drop_table("pipeline")
    op.drop_table("component")
