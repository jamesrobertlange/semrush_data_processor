.PHONY: help install run dev prod clean

help:
	@echo "SEMrush Data Processor - Commands"
	@echo "=================================="
	@echo "make install    - Install dependencies"
	@echo "make run        - Run development server"
	@echo "make dev        - Run development server"
	@echo "make prod       - Run production server"
	@echo "make clean      - Remove cache files"

install:
	uv sync
	mkdir -p uploads

run: dev

dev:
	uv run flask run --debug

prod:
	@uv pip show gunicorn > /dev/null 2>&1 || uv add gunicorn
	uv run gunicorn -w 4 -b 0.0.0.0:8000 app:app

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
