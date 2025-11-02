# Makefile for Image Search API

.PHONY: help build up down logs stop restart test lint format

help:
	@echo "Available commands:"
	@echo "  make build       - Build Docker images"
	@echo "  make up          - Start services with Docker Compose"
	@echo "  make down        - Stop and remove containers"
	@echo "  make logs        - View logs from all services"
	@echo "  make stop        - Stop containers without removing"
	@echo "  make restart     - Restart services"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make install     - Install dependencies"
	@echo "  make shell       - Open shell in API container"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 5
	@echo "Services started. Check health at http://localhost:8000/api/v1/health"

down:
	docker-compose down

logs:
	docker-compose logs -f

stop:
	docker-compose stop

restart:
	docker-compose restart

test:
	pytest tests/ -v --tb=short

lint:
	flake8 app tests --max-line-length=120
	pylint app tests

format:
	black app tests
	isort app tests

install:
	pip install -r requirements.txt

shell:
	docker-compose exec api /bin/bash

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

status:
	docker-compose ps

health:
	curl -s http://localhost:8000/api/v1/health | jq .

docs:
	@echo "API Documentation available at:"
	@echo "  Swagger UI: http://localhost:8000/docs"
	@echo "  ReDoc: http://localhost:8000/redoc"
	@echo "  OpenAPI: http://localhost:8000/openapi.json"

.DEFAULT_GOAL := help
