"""add market price snapshots

Revision ID: 0003_market_price_snapshots
Revises: 0002_document_chunks
Create Date: 2026-02-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_market_price_snapshots"
down_revision: Union[str, None] = "0002_document_chunks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_price_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("interval", sa.String(length=16), nullable=False),
        sa.Column("ts_utc", sa.DateTime(), nullable=False),
        sa.Column("open", sa.Float(), nullable=False),
        sa.Column("high", sa.Float(), nullable=False),
        sa.Column("low", sa.Float(), nullable=False),
        sa.Column("close", sa.Float(), nullable=False),
        sa.Column("volume", sa.Float(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_market_price_snapshots_ticker_ts_utc",
        "market_price_snapshots",
        ["ticker", "ts_utc"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_market_price_snapshots_ticker_ts_utc", table_name="market_price_snapshots")
    op.drop_table("market_price_snapshots")
