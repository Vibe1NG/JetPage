#!/bin/bash
set -e

# Task runner script for JetPage development

case "$1" in
    run)
        uv run jetpage
        ;;
    test)
        uv run pytest tests/ -v --ignore=tests/e2e
        uv run behave features/
        ;;
    test-e2e)
        uv run playwright install chromium
        uv run pytest tests/e2e/ -v
        ;;
    lint)
        uv run ruff check jetpage/ features/ tests/ --fix
        ;;
    format)
        uv run ruff format jetpage/ features/ tests/
        ;;
    typing)
        uv run pyright jetpage/
        ;;
    build)
        podman build -t jetpage -f Containerfile .
        ;;
    *)
        echo "Usage: $0 {run|test|test-e2e|lint|format|typing|build}"
        exit 1
esac
