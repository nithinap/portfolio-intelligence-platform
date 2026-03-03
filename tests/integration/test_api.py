from fastapi.testclient import TestClient
from sqlalchemy import func, select

from src.api.main import app
from src.common.db import SessionLocal
from src.core.models import Signal


def test_health_endpoints():
    with TestClient(app) as client:
        live = client.get("/health/live")
        ready = client.get("/health/ready")

        assert live.status_code == 200
        assert live.json() == {"status": "ok"}
        assert ready.status_code == 200
        assert ready.json() == {"status": "ready"}


def test_version_endpoint():
    with TestClient(app) as client:
        resp = client.get("/version")
        assert resp.status_code == 200
        body = resp.json()
        assert "app_name" in body
        assert "app_version" in body
        assert "git_sha" in body


def test_documents_ingest_endpoint():
    payload = {
        "documents": [
            {
                "source": "unit-test-news",
                "ticker": "AAPL",
                "title": "AAPL earnings momentum",
                "content": "Apple revenue grew and margins improved. Guidance remained strong.",
                "metadata": {"section": "earnings"},
            }
        ]
    }
    with TestClient(app) as client:
        resp = client.post("/documents/ingest", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["documents_ingested"] == 1
        assert body["chunks_ingested"] >= 1


def test_qa_endpoint_returns_citations():
    with TestClient(app) as client:
        ingest_payload = {
            "documents": [
                {
                    "source": "unit-test-qa",
                    "ticker": "MSFT",
                    "title": "MSFT cloud demand",
                    "content": (
                        "Microsoft cloud demand accelerated with stronger enterprise adoption."
                    ),
                }
            ]
        }
        ingest = client.post("/documents/ingest", json=ingest_payload)
        assert ingest.status_code == 200

        qa_payload = {
            "question": "What do documents say about Microsoft cloud demand?",
            "source": "unit-test-qa",
            "ticker": "MSFT",
        }
        qa = client.post("/qa", json=qa_payload)
        assert qa.status_code == 200
        body = qa.json()
        assert body["confidence"] > 0
        assert body["answer_provider"] in {"deterministic", "deterministic-fallback", "openai"}
        assert len(body["citations"]) >= 1


def test_market_snapshot_endpoints():
    with TestClient(app) as client:
        fetch = client.post("/market/snapshots/fetch")
        assert fetch.status_code == 200
        fetch_body = fetch.json()
        assert fetch_body["records_processed"] >= 1

        list_resp = client.get("/market/snapshots?ticker=AAPL&limit=5")
        assert list_resp.status_code == 200
        rows = list_resp.json()
        assert len(rows) >= 1
        assert rows[0]["ticker"] == "AAPL"


def test_qa_evaluate_endpoint():
    with TestClient(app) as client:
        ingest_payload = {
            "documents": [
                {
                    "source": "unit-test-eval",
                    "ticker": "AAPL",
                    "title": "AAPL margins",
                    "content": "Apple margins improved while guidance for revenue remained strong.",
                }
            ]
        }
        ingest = client.post("/documents/ingest", json=ingest_payload)
        assert ingest.status_code == 200

        eval_payload = {
            "cases": [
                {
                    "question": "What do documents say about Apple margins?",
                    "ticker": "AAPL",
                    "source": "unit-test-eval",
                    "min_citations": 1,
                    "min_confidence": 0.1,
                }
            ]
        }
        resp = client.post("/qa/evaluate", json=eval_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_cases"] == 1
        assert body["citation_coverage"] >= 1.0
        assert body["cases"][0]["passed"] is True


def test_sentiment_compute_endpoint():
    with TestClient(app) as client:
        ingest_payload = {
            "documents": [
                {
                    "source": "unit-test-sentiment",
                    "ticker": "NVDA",
                    "title": "Positive trend",
                    "content": "Strong growth accelerated and margins improved with record demand.",
                }
            ]
        }
        ingest = client.post("/documents/ingest", json=ingest_payload)
        assert ingest.status_code == 200

        compute_payload = {"ticker": "NVDA", "source": "unit-test-sentiment"}
        compute = client.post("/signals/sentiment/compute", json=compute_payload)
        assert compute.status_code == 200
        body = compute.json()
        assert body["rows_written"] >= 1
        assert "provider_counts" in body
        assert len(body["provider_counts"]) >= 1

    with SessionLocal() as session:
        total = session.scalar(
            select(func.count()).select_from(Signal).where(Signal.signal_type == "sentiment_daily")
        )
        assert total is not None
        assert total >= 1


def test_chunking_benchmark_endpoint():
    payload = {
        "threshold": 0.3,
        "cases": [
            {
                "question": "What is the trend in Apple margins?",
                "content": (
                    "Apple margins improved in the quarter while revenue also grew and "
                    "guidance remained strong."
                ),
            },
            {
                "question": "How is Microsoft cloud demand changing?",
                "content": (
                    "Microsoft reported cloud demand acceleration from enterprise customers "
                    "with stronger usage trends."
                ),
            },
        ],
    }
    with TestClient(app) as client:
        resp = client.post("/qa/chunking/benchmark", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert body["winner"] in {"simple", "token"}
        assert len(body["metrics"]) == 2
