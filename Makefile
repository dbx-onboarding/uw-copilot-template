# UW CoPilot — Common development operations.
# Usage: make <target>

.PHONY: install install-dev test lint format deploy setup intake config-check

# ─── Local development ────────────────────────────────────────────────────────

install:
	pip install -e .

install-dev:
	pip install -e ".[dev,app]"

test:
	PYTHONDONTWRITEBYTECODE=1 pytest tests/ -v \
	  -p no:cacheprovider --import-mode=importlib \
	  --cov=uw_copilot --cov-report=term-missing

lint:
	ruff check src/ tests/

format:
	ruff format src/ tests/

# ─── Databricks bundle ────────────────────────────────────────────────────────

deploy:
	databricks bundle deploy

deploy-prod:
	databricks bundle deploy --target prod

# ─── One-time setup ───────────────────────────────────────────────────────────

setup:
	@echo "Running one-time pipeline setup job..."
	databricks jobs run-now --job-name uw-copilot-pipeline-setup

# ─── Day-to-day operations ────────────────────────────────────────────────────

intake:
	@echo "Triggering intake job manually..."
	databricks jobs run-now --job-name uw-copilot-intake

infra-start:
	databricks jobs run-now --job-name uw-copilot-infra-start

infra-stop:
	databricks jobs run-now --job-name uw-copilot-infra-stop

app-deploy:
	databricks jobs run-now --job-name uw-copilot-app-deploy

# ─── Config helpers ───────────────────────────────────────────────────────────

config-check:
	@python -c "from uw_copilot.config import Config; c = Config(); c.print_summary()"

show-names:
	@python scripts/generate_job_names.py
