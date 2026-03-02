# Current Status And Next Steps

Last updated: 2026-03-01 22:35:24 MST

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
- Added chunker provider interface:
  - `SimpleChunker` (character windows) and `TokenChunker` (token windows).
  - Configurable via environment/profile settings.
- Added grounded QA service and API route:
  - `POST /qa` returns answer, confidence, and citations.
- Added QA evaluation checks:
  - `POST /qa/evaluate` returns pass rate, citation coverage, and per-case failures.
- Added sentiment signal baseline:
  - `POST /signals/sentiment/compute` aggregates document sentiment into `signals`.
  - Baseline scoring uses deterministic positive/negative keyword lexicon.
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
- Benchmark current chunking defaults on retrieval quality and latency.
- Decide default provider by environment (`simple` for local, `token` for production).

2. Add model-backed QA generation.
- Keep citation and filter constraints as hard requirements.
- Compare answer quality vs deterministic baseline.

3. Improve sentiment scoring quality.
- Replace lexicon-only baseline with model-based scoring.
- Add calibration and backtests for sentiment utility.

## Suggested Immediate Execution Order

1. Chunking benchmark and default-provider decision.
2. Model-backed QA generation with grounding constraints.
3. Sentiment scoring upgrade and validation.
