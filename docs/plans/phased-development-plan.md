# Phased Development Plan

## Objective
Build an extensible AI-assisted stock portfolio and trading system that starts as decision-support and progressively adds agentic analysis, feedback learning, and controlled automation.

## Non-Goals (Initial Phases)
- Fully autonomous live trading from day one
- Complex RL-based optimization before baseline signal quality is proven
- Premature microservice split without load/scaling evidence

## Core Architecture (Target State)

### 1) Data Layer
- Ingestion connectors for market data, fundamentals, filings, and news.
- Storage split:
  - Relational DB for portfolio, orders, audit trails, configs
  - Time-series store for prices/features
  - Vector store for document embeddings
- Symbol/entity normalization + point-in-time snapshot discipline.

### 2) Intelligence Layer
- RAG for grounded Q&A over portfolio-relevant documents.
- Signal engines:
  - Fundamentals (long-horizon health/value)
  - Technical (short-horizon momentum/mean-reversion)
  - Sentiment (news/social polarity and trend)
- Orchestrated analyst workflow to generate consolidated analysis.

### 3) Decision Layer
- Policy engine converts signals to recommendations with confidence and rationale.
- Risk engine enforces hard constraints (position sizing, exposure caps, liquidity limits).
- Human approval gate before any execution path in early phases.

### 4) Execution Layer
- Broker abstraction interface.
- Paper execution adapter first; live adapter optional later.
- Full traceability: input data -> signal versions -> decision -> order event.

### 5) Evaluation Layer
- Backtesting and walk-forward validation.
- Drift and source-quality monitoring.
- Versioned prompts/models/feature sets for reproducibility.

## Phases

## Phase 0: Platform Foundation (2-3 weeks)
### Scope
- Repo skeleton, service boundaries, config management.
- Database schema draft and migration pipeline.
- Scheduler/job framework and observability baseline.

### Deliverables
- Running API skeleton + health endpoints.
- Ingestion job runner with stub connectors.
- Logging, metrics, and trace IDs across modules.

### Exit Criteria
- Deterministic local runbook.
- Ingestion jobs execute on schedule and write audit logs.

## Phase 1: Portfolio Q&A + Basic RAG (3-4 weeks)
### Scope
- Ingest documents (filings/news) and market snapshots.
- Build chunking/embedding/index pipeline.
- RAG QA endpoint with citations and confidence.

### Deliverables
- `/qa` API answering portfolio-specific queries.
- Retrieval trace showing cited source chunks.
- Basic sentiment classification pipeline.

### Exit Criteria
- Answers are grounded (with source references).
- Hallucination rate reduced via retrieval constraints.

## Phase 2: Multi-Agent Analysis (4-6 weeks)
### Scope
- Implement technical/fundamental/sentiment signal modules.
- Add analyst agent roles and orchestration flow.
- Produce short-term and long-term recommendation reports.

### Deliverables
- Unified analysis output schema.
- Agent orchestration with visible intermediate reasoning artifacts.
- Deterministic unit tests for indicators and signal transforms.

### Exit Criteria
- Consistent report generation across selected tickers.
- Analysis latency and failure rates within target bounds.

## Phase 3: Feedback & Adaptive Weighting (4-6 weeks)
### Scope
- Prediction-vs-realized-return tracking.
- Source/signal weighting based on measured historical utility.
- Hybrid retrieval expansion (vector + entity graph metadata).

### Deliverables
- Feedback store with prediction outcomes.
- Adaptive weighting engine (start with transparent Bayesian/EMA scoring).
- Performance dashboard with lift vs static baseline.

### Exit Criteria
- Measurable outperformance against static-weight baseline in paper evaluation.
- Stable weighting behavior across market regimes tested.

## Phase 4: Risk, Paper Trading, Controlled Automation (4-8 weeks)
### Scope
- Risk policy enforcement and pre-trade checks.
- Paper trading integration with order lifecycle tracking.
- Optional constrained automation for low-risk scenarios.

### Deliverables
- Trade proposal -> risk gate -> approval -> paper execution pipeline.
- Drawdown and exposure monitoring alerts.
- Live-trading adapter contract (feature-flagged/off by default).

### Exit Criteria
- No risk rule violations in paper mode during evaluation window.
- Stable operational metrics and audit completeness.

## Why This Sequence
- Prioritizes data quality and traceability before optimization.
- Avoids expensive RL complexity until baseline system behavior is reliable.
- Keeps architecture extensible while preserving speed of iteration.

## Future Extensions
- RL/PPO for policy improvement after robust baseline benchmarks.
- LoRA/QLoRA fine-tuning for finance-specific classification subtasks.
- Multi-broker support and optional execution automation tiers.
