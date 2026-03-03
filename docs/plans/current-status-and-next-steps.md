# Current Status And Next Steps

Last updated: 2026-03-02 22:18:58 MST

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
- Added chunking benchmark endpoint:
  - `POST /qa/chunking/benchmark` compares simple vs token chunkers on overlap/pass-rate and latency metrics.
- Added grounded QA service and API route:
  - `POST /qa` returns answer, confidence, and citations.
- Added model-backed QA generation option:
  - Configurable provider (`deterministic` or `openai`) with grounded prompt constraints.
  - Automatic deterministic fallback when provider call fails or API key is missing.
- Added QA evaluation checks:
  - `POST /qa/evaluate` returns pass rate, citation coverage, and per-case failures.
- Added sentiment signal baseline:
  - `POST /signals/sentiment/compute` aggregates document sentiment into `signals`.
  - Supports configurable providers (`lexicon`, `openai`) with lexicon fallback.
- Added recommendation outcome tracking:
  - `POST /recommendations/outcomes` records realized outcomes for recommendation decisions.
  - `GET /recommendations/outcomes/summary` reports hit rate, return stats, calibration gap, and drift.
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
- Sentiment calibration framework and utility backtests.
- Phase 2+ modules (signals/agents/policy/risk/execution/backtesting/monitoring logic).

## Next Steps / Task Backlog

1. Expand chunking benchmark coverage.
- Add portfolio-specific eval corpora and thresholds.
- Use benchmark outputs to set and enforce environment defaults.

2. Add sentiment calibration and backtests.
- Compare provider outputs against realized move labels.
- Track stability and drift of sentiment signal quality.

3. Improve outcome attribution and dashboards.
- Break down recommendation outcomes by source, signal type, and horizon.
- Add trend dashboards for hit rate and calibration drift.

## Suggested Immediate Execution Order

1. Chunking benchmark expansion and default policy automation.
2. Sentiment calibration/backtesting pipeline.
3. Outcome attribution and dashboarding.
