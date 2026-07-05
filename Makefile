.PHONY: run test lint

run:
	uv run streamlit run main.py

test:
	uv run pytest

lint:
	uv run ruff check . && uv run ruff format --check .
