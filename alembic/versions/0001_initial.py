"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-02-14
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "portfolios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "positions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("portfolio_id", sa.Integer(), sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("avg_cost", sa.Float(), nullable=False),
        sa.Column("as_of", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("portfolio_id", sa.Integer(), sa.ForeignKey("portfolios.id"), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.Column("executed_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "embedding_metadata",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("chunk_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("vector_provider", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
    )
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("signal_type", sa.String(length=32), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("as_of", sa.DateTime(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
    )
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("ticker", sa.String(length=16), nullable=False),
        sa.Column("horizon", sa.String(length=16), nullable=False),
        sa.Column("action", sa.String(length=8), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "job_audit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("job_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("records_processed", sa.Integer(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("job_audit")
    op.drop_table("audit_events")
    op.drop_table("recommendations")
    op.drop_table("signals")
    op.drop_table("embedding_metadata")
    op.drop_table("documents")
    op.drop_table("transactions")
    op.drop_table("positions")
    op.drop_table("portfolios")
