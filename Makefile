PYTHON ?= python

setup: install migrate seed

install:
	$(PYTHON) -m pip install -r apps/api/requirements-dev.txt
	npm install --prefix apps/web

migrate:
	cd apps/api && $(PYTHON) -m alembic upgrade head

seed:
	cd apps/api && $(PYTHON) -m app.seed

api:
	cd apps/api && $(PYTHON) -m uvicorn app.main:app --reload --port 8000

web:
	npm --prefix apps/web run dev

dev:
	docker compose -f infrastructure/docker-compose.yml up --build

test:
	$(PYTHON) -m pytest
	npm --prefix apps/web run test

lint:
	$(PYTHON) -m ruff check apps/api
	npm --prefix apps/web run lint

typecheck:
	$(PYTHON) -m mypy apps/api/app
	npm --prefix apps/web run typecheck

reset-db:
	cd apps/api && $(PYTHON) -m alembic downgrade base
	cd apps/api && $(PYTHON) -m alembic upgrade head
	cd apps/api && $(PYTHON) -m app.seed
