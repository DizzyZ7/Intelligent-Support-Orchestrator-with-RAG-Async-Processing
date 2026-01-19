mkdir -p app/{api,core,services,worker} data/knowledge_base docker tests
touch app/__init__.py app/api/__init__.py app/core/__init__.py app/services/__init__.py app/worker/__init__.py
touch app/api/routes.py app/core/config.py app/core/celery_app.py
touch app/services/ingestion.py app/services/llm_service.py app/services/zendesk.py
touch app/worker/tasks.py
touch .env .env.example .gitignore docker-compose.yml pyproject.toml README.md
