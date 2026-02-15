from fastapi.testclient import TestClient

from src.api.main import app


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
        assert len(body["citations"]) >= 1
