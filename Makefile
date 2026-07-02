.PHONY: help install migrate seed test lint format clean docker-build docker-up docker-down

help:
	@echo "Comandos disponíveis:"
	@echo "  make install        - Instala dependências"
	@echo "  make migrate        - Executa migrações"
	@echo "  make seed           - Popula banco com dados de teste"
	@echo "  make test           - Executa testes"
	@echo "  make test-cov       - Executa testes com cobertura"
	@echo "  make lint           - Executa linter"
	@echo "  make format         - Formata código"
	@echo "  make clean          - Remove arquivos gerados"
	@echo "  make runserver      - Inicia servidor de desenvolvimento"
	@echo "  make celery         - Inicia worker Celery"
	@echo "  make celery-beat    - Inicia scheduler Celery"
	@echo "  make docker-build   - Constrói imagens Docker"
	@echo "  make docker-up      - Inicia containers"
	@echo "  make docker-down    - Para containers"

install:
	pip install -r requirements.txt

migrate:
	python manage.py makemigrations
	python manage.py migrate

seed:
	python manage.py shell < scripts/seed.py

test:
	pytest

test-cov:
	pytest --cov=apps --cov=services --cov=tasks --cov-report=html --cov-report=term-missing

lint:
	flake8 apps services tasks config

format:
	black apps services tasks config tests

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/

runserver:
	python manage.py runserver 0.0.0.0:8000

celery:
	celery -A config worker -l info

celery-beat:
	celery -A config beat -l info

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f web
create-superuser:
	python manage.py shell -c 'from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser("admin", "admin@example.com", "admin123")'
