"""add recommendation outcomes

Revision ID: 0004_recommendation_outcomes
Revises: 0003_market_price_snapshots
Create Date: 2026-03-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_recommendation_outcomes"
down_revision: Union[str, None] = "0003_market_price_snapshots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recommendation_outcomes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "recommendation_id",
            sa.Integer(),
            sa.ForeignKey("recommendations.id"),
            nullable=True,
        ),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("horizon", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=8), nullable=False),
        sa.Column("expected_confidence", sa.Float(), nullable=False),
        sa.Column("realized_return", sa.Float(), nullable=False),
        sa.Column("window_days", sa.Integer(), nullable=False),
        sa.Column("outcome_label", sa.String(length=12), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("realized_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_recommendation_outcomes_ticker_realized_at",
        "recommendation_outcomes",
        ["ticker", "realized_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_recommendation_outcomes_ticker_realized_at",
        table_name="recommendation_outcomes",
    )
    op.drop_table("recommendation_outcomes")
