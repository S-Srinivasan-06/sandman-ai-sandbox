.PHONY: install lint format test run clean

install:
	pip install -e .

lint:
	ruff check src/ tests/

format:
	black src/ tests/
	ruff check src/ tests/ --fix

test:
	pytest tests/ -v --tb=short

run:
	python -m src.cli.entry

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf sandbox_workspace/* outputs/* logs/*
