# AI-Assisted Stock Portfolio & Trading System

This repository contains a modular backend architecture for:
- Portfolio Q&A with grounded answers (RAG)
- Short/long-horizon analysis from multiple signal types
- Risk-aware trade proposal workflows
- Paper-trading first, automation later

## Project Status
Phase 0 baseline is complete. Phase 1 is in progress with a working vertical slice.

Current capabilities:
- FastAPI baseline endpoints: `/health/live`, `/health/ready`, `/version`, `/metrics`
- Document ingestion with chunking: `POST /documents/ingest`
- Grounded Q&A with citations and confidence: `POST /qa`
- Lexical retrieval with ticker/source/date filtering
- Database migrations, seed data, scheduler framework, and job audit logging
- CI checks for lint and tests

Known limitations (current state):
- Market/news/filings connectors are still stubs
- Retrieval is lexical fallback (no real embedding/vector index yet)
- QA answer synthesis is deterministic (no LLM integration yet)
- Sentiment pipeline and Phase 1 evaluation metrics are not implemented yet

Detailed running status and task tracker:
- `docs/plans/current-status-and-next-steps.md`

## Quickstart (Phase 0)
1. `cp .env.example .env`
2. `make setup`
3. `make migrate`
4. `make seed-db`
5. `make run-api`

Validation:
- `make lint`
- `make test`
- `make run-jobs`

## Dev Test Endpoints
- `GET /health/live`
- `GET /health/ready`
- `GET /version`
- `GET /metrics`
- `POST /documents/ingest`
- `POST /qa`

Example ingestion request:

```bash
curl -X POST http://localhost:8000/documents/ingest \
  -H "content-type: application/json" \
  -d '{
    "documents": [
      {
        "source": "news",
        "ticker": "AAPL",
        "title": "AAPL Earnings Update",
        "content": "Revenue and margins improved while guidance remained strong."
      }
    ]
  }'
```

Example QA request:

```bash
curl -X POST http://localhost:8000/qa \
  -H "content-type: application/json" \
  -d '{
    "question": "What do filings and news say about AAPL momentum?",
    "ticker": "AAPL",
    "top_k": 5
  }'
```

## Architecture Principles
- Decision support first; avoid direct auto-execution initially.
- Event- and snapshot-based data model with full traceability.
- Clear module boundaries (ingestion, reasoning, policy, risk, execution, evaluation).
- Offline evaluation + paper trading gates before live automation.

## Folder Structure

```text
.
├── docs/
│   ├── adr/                        # Architecture decision records
│   └── plans/
│       ├── phased-development-plan.md
│       └── implementation-backlog.md
├── src/
│   ├── api/                        # FastAPI routes and app wiring
│   ├── core/                       # Domain models, services, shared business logic
│   ├── common/                     # Utilities, logging, config loader
│   ├── data_ingestion/
│   │   ├── connectors/             # Source adapters (prices, filings, news, etc.)
│   │   ├── pipelines/              # ETL/ELT orchestration
│   │   └── schemas/                # Ingestion schemas and contracts
│   ├── rag/                        # Chunking, embedding, retrieval, grounding
│   ├── signals/                    # Technical/fundamental/sentiment features
│   ├── agents/                     # Analyst/report agents and orchestration graph
│   ├── policies/                   # Decision policy and recommendation logic
│   ├── risk/                       # Risk constraints and pre-trade checks
│   ├── execution/                  # Broker abstraction + paper/live adapters
│   ├── backtesting/                # Historical sim, walk-forward, attribution
│   └── monitoring/                 # Drift, performance, source quality metrics
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── infra/
│   ├── docker/
│   └── terraform/
├── configs/                        # Environment-specific YAML/TOML configs
├── scripts/                        # Operational scripts (bootstrap, jobs, maintenance)
├── notebooks/                      # Research notebooks (non-production)
├── data/
│   ├── raw/                        # Immutable landing zone
│   ├── processed/                  # Cleaned/normalized datasets
│   └── snapshots/                  # Point-in-time datasets for reproducibility
└── .github/workflows/              # CI/CD pipelines
```

## Suggested Initial Stack
- Python + FastAPI
- PostgreSQL (optionally Timescale extension) + Redis
- pgvector or Pinecone for embeddings
- Prefect/Temporal for scheduled workflows
- MLflow (or W&B) for experiment/version tracking
- OpenTelemetry + Prometheus/Grafana for observability

## Immediate Priorities
1. Add market data provider abstraction and initial Yahoo Finance connector.
2. Persist normalized OHLCV snapshots with migration + ingestion job wiring.
3. Replace stub market snapshot job with real connector-backed ingestion.
4. Add embedding/vector retrieval path while preserving current filter contract.
