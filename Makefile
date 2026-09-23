.PHONY: dev backend frontend install test

install:
	pip install --break-system-packages -r backend/requirements.txt
	cd frontend && npm install

backend:
	python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm run dev

test:
	python3 -m pytest tests/ -v

dev:
	@echo "Run 'make backend' and 'make frontend' in two separate terminals."
