# Current Status And Next Steps

Last updated: 2026-03-01 22:07:24 MST

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

### Phase 1 (In Progress) - Vertical Slice Delivered
- Added document chunk storage model and migration:
  - `document_chunks` table with chunk metadata.
- Added document ingestion pipeline:
  - Accepts documents and writes documents + chunks + sparse embedding metadata.
- Added retrieval service:
  - Sparse embedding scoring with lexical fallback.
  - Filters by ticker/source/date range preserved.
- Added grounded QA service and API route:
  - `POST /qa` returns answer, confidence, and citations.
- Added ingestion API route:
  - `POST /documents/ingest`.
- Added integration tests covering ingestion and QA behavior.
- Validation status:
  - `make lint` passing.
  - `make test` passing.

### Additional Progress (Post-Phase-1 Slice)
- Added market data provider abstraction:
  - `MarketDataProvider` interface with provider selection via settings.
  - Implemented `StubMarketDataProvider` (default) and `YahooFinanceProvider` (optional).
- Added market snapshot persistence:
  - New table `market_price_snapshots` + migration.
  - Pipeline write path for normalized OHLCV bars.
- Replaced stub market job behavior:
  - `run_market_snapshot_job` now fetches provider bars and writes snapshot rows.
  - Scheduler audit + metrics behavior preserved.
- Added integration test for market snapshot persistence.

## What Is Not Built Yet
- Real market/news/filings connectors (current jobs are stubs).
- Real embedding model calls and vector index writes.
- LLM answer generation for QA (current answer synthesis is deterministic).
- Sentiment pipeline and Phase 1 evaluation framework.
- Phase 2+ modules (signals/agents/policy/risk/execution/backtesting/monitoring logic).

## Next Steps / Task Backlog

1. Improve chunking architecture.
- Introduce a chunker interface (`SimpleChunker`, `TokenChunker`).
- Keep current chunker as default until token-based variant is benchmarked.

2. Add Phase 1 QA quality checks.
- Build small curated QA fixture set.
- Track citation coverage and consistency metrics.

3. Add sentiment pipeline baseline.
- Ingest sentiment signals by ticker/source/date.
- Persist aggregates for downstream Phase 2 signal modules.

## Suggested Immediate Execution Order

1. Chunker interface + token chunking experiment.
2. QA evaluation checks and reporting.
3. Sentiment pipeline baseline with persisted aggregates.
