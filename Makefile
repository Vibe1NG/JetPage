.PHONY: run test test-e2e lint format build

run:
	poetry run python -m sitegen.main

test:
	poetry run pytest tests/ -v --ignore=tests/e2e
	poetry run behave features/

test-e2e:
	poetry run playwright install chromium
	poetry run pytest tests/e2e/ -v

lint:
	poetry run ruff check sitegen/ features/ tests/

format:
	poetry run ruff format sitegen/ features/ tests/

build:
	podman build -t sitegen -f Containerfile .
