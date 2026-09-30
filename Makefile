.PHONY: setup dev-backend dev-frontend test lint check

setup:
	cd backend && uv sync
	cd frontend && npm install

dev-backend:
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test:
	cd backend && uv run pytest -q

lint:
	cd backend && uv run ruff check app tests
	cd frontend && npm run lint

check: lint test
	cd frontend && npm run build
