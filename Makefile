.PHONY: setup lint test run-api run-jobs seed-db migrate revision

setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip && pip install -e .[dev]

lint:
	. .venv/bin/activate && ruff check src tests

test:
	. .venv/bin/activate && PYTHONPATH=. pytest

run-api:
	. .venv/bin/activate && uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

run-jobs:
	. .venv/bin/activate && python -m src.data_ingestion.pipelines.scheduler

seed-db:
	. .venv/bin/activate && python scripts/seed_db.py

migrate:
	. .venv/bin/activate && alembic upgrade head

revision:
	. .venv/bin/activate && alembic revision --autogenerate -m "schema update"
