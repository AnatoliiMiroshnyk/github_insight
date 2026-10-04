.PHONY: install run test lint check
all: check
install:
	python -m pip install -e ".[dev]"
run:
	uvicorn github_insight.main:app --reload
lint:
	ruff check src tests
test:
	pytest --cov=github_insight --cov-report=term-missing
check: lint test
