# Implementation Backlog

## Phase 0 Backlog (Start Here)

1. Project bootstrap
- Add `pyproject.toml` with core dependencies (FastAPI, pydantic, SQLAlchemy, Alembic, pandas, numpy, httpx, structlog).
- Add `Makefile` targets: `setup`, `lint`, `test`, `run-api`, `run-jobs`.
- Add `.env.example` for API keys and DB/vector endpoints.

2. Configuration system
- Implement typed settings in `src/common`.
- Add environment profiles (local/dev/prod) in `configs/`.
- Define secret handling strategy (env vars only, no hardcoded secrets).

3. Database baseline
- Design initial schema: portfolio, positions, transactions, documents, embeddings metadata, signals, recommendations, audit events.
- Create Alembic migrations.
- Add seed script for sample portfolio data.

4. Job orchestration baseline
- Build ingestion scheduler interface.
- Add stub jobs: market snapshot fetch, news fetch, filings fetch.
- Ensure every run writes a job audit record.

5. API baseline
- Implement health endpoints and readiness checks.
- Add version endpoint exposing git SHA/app version.
- Add structured error response model.

6. Observability baseline
- Add structured logging with correlation IDs.
- Add metrics for job success/failure, latency, throughput.
- Add tracing hooks across API and jobs.

7. Testing baseline
- Unit test harness and fixtures.
- Integration test setup with disposable DB.
- CI workflow for lint + tests.

## Phase 1 Backlog

1. Document ingestion and processing
- Implement parsers/chunkers for filings/news content.
- Add chunk metadata schema (source, timestamp, ticker, section).

2. Embeddings and retrieval
- Implement embedding pipeline and vector index writes.
- Implement retrieval API with filtering by ticker/date/source.

3. Portfolio QA endpoint
- Add `/qa` route that composes retrieval + LLM answer.
- Require source citation payload in every answer.

4. Basic sentiment pipeline
- Integrate finance sentiment model inference.
- Persist daily sentiment aggregates by ticker/source.

5. Evaluation checks
- Add QA quality checks on a curated question set.
- Track citation coverage and answer consistency.

## Phase 2 Backlog

1. Signal modules
- Technical indicators (RSI, MACD, moving averages, volatility).
- Fundamental factors (growth, margins, valuation snapshots).
- Sentiment trend features (level, momentum, disagreement).

2. Agent orchestration
- Implement analyst role interfaces and contract schema.
- Add orchestrator to combine analyst outputs into single report.

3. Recommendation schema
- Standardize output: horizon, action, confidence, rationale, assumptions, invalidation triggers.

4. Guarded reasoning traces
- Persist intermediate artifacts for debugging and audits.

## Phase 3 Backlog

1. Feedback dataset
- Store predictions with time horizon and realized outcomes.

2. Weighting engine
- Start with transparent adaptive weighting (EMA/Bayesian scoring).
- Add source reliability dashboard.

3. Hybrid retrieval enhancements
- Add entity extraction and relationship metadata.
- Use hybrid ranking over vector + structured metadata.

## Phase 4 Backlog

1. Risk engine
- Implement pre-trade rules: max position size, total exposure, concentration, liquidity threshold.

2. Paper trading integration
- Build broker adapter and paper order lifecycle tracking.

3. Approval workflow
- Add explicit human approval gate for order execution.

4. Controlled automation
- Enable optional auto-submit only for predefined low-risk policy set.

## Definition of Done (Cross-Phase)
- Every decision includes traceable inputs and versioned logic metadata.
- Tests cover critical computations and integration boundaries.
- Metrics and logs are sufficient to diagnose failures quickly.
- Security checks enforce secret handling and permission boundaries.
