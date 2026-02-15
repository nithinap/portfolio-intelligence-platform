# Current Status And Next Steps

Last updated: 2026-02-15 15:20:42 MST

## Progress Summary

### Phase 0 (Foundation) - Complete
- FastAPI service baseline is working with:
  - `GET /health/live`
  - `GET /health/ready`
  - `GET /version`
  - `GET /metrics`
- Core platform pieces are in place:
  - Typed settings with env + profile YAML support.
  - Structured logging and correlation IDs.
  - Prometheus metrics middleware and tracing setup.
  - SQLAlchemy + Alembic database baseline.
  - Scheduler framework and job audit logging.
- Database schema exists for key entities:
  - portfolios, positions, transactions
  - documents, embedding metadata
  - signals, recommendations
  - audit events, job audit
- Local developer workflow and CI are set:
  - `Makefile` commands for setup/lint/test/migrate/run.
  - GitHub Actions CI running lint + tests.

### Phase 1 (In Progress) - Initial Vertical Slice Delivered
- Added document chunk storage model and migration:
  - `document_chunks` table with chunk metadata.
- Added document ingestion pipeline:
  - Accepts documents and writes documents + chunks + embedding metadata stubs.
- Added retrieval service:
  - Lexical ranking with filters by ticker/source/date range.
- Added grounded QA service and API route:
  - `POST /qa` returns answer, confidence, and citations.
- Added ingestion API route:
  - `POST /documents/ingest`.
- Added integration tests covering ingestion and QA behavior.
- Validation status:
  - `make lint` passing.
  - `make test` passing (6 tests).

## What Is Not Built Yet
- Real market/news/filings connectors (current jobs are stubs).
- Real embedding model calls and vector index writes.
- LLM answer generation for QA (current answer synthesis is deterministic).
- Sentiment pipeline and Phase 1 evaluation framework.
- Phase 2+ modules (signals/agents/policy/risk/execution/backtesting/monitoring logic).

## Next Steps / Task Backlog

1. Implement market data provider abstraction.
- Add `MarketDataProvider` interface under ingestion connectors.
- Keep ingestion pipeline decoupled from specific data vendors.

2. Add first real connector (Yahoo Finance for development).
- Implement connector methods for OHLCV snapshots.
- Normalize symbols/timestamps and map to canonical schema.

3. Persist market snapshots.
- Add new DB table + Alembic migration for price bars.
- Write ingestion pipeline + audit records for snapshot runs.

4. Replace stub `run_market_snapshot_job`.
- Wire scheduler job to call connector + persistence layer.
- Keep existing `JobAudit` logging and metrics.

5. Upgrade retrieval from lexical stub to vector-capable design.
- Add embedding provider interface.
- Store embeddings/vector references and keep current retrieval filters.
- Preserve deterministic fallback mode for local tests.

6. Improve chunking architecture.
- Introduce a chunker interface (`SimpleChunker`, `TokenChunker`).
- Keep current chunker as default until token-based variant is benchmarked.

7. Add Phase 1 QA quality checks.
- Build small curated QA fixture set.
- Track citation coverage and consistency metrics.

8. Add sentiment pipeline baseline.
- Ingest sentiment signals by ticker/source/date.
- Persist aggregates for downstream Phase 2 signal modules.

## Suggested Immediate Execution Order

1. Market data provider interface + Yahoo connector.
2. Price snapshot schema + ingestion pipeline wiring.
3. Scheduler integration replacing stub market job.
4. Retrieval/embedding interface upgrade.
5. Chunker interface + token chunking experiment.
