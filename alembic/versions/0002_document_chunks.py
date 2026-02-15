"""add document chunks

Revision ID: 0002_document_chunks
Revises: 0001_initial
Create Date: 2026-02-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_document_chunks"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id"), nullable=False),
        sa.Column("chunk_id", sa.String(length=64), nullable=False, unique=True),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("ticker", sa.String(length=16), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("document_chunks")
