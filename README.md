# Intelligent Support Orchestrator (RAG + Async)

An enterprise-grade support automation engine that uses RAG (Retrieval-Augmented Generation) 
to answer customer tickets based on internal documentation.

## 🛠 Tech Stack
- **FastAPI**: Asynchronous API Gateway.
- **Celery + Redis**: Distributed task queue for LLM processing.
- **Qdrant**: Vector database for semantic search.
- **LangChain**: Orchestrating the RAG pipeline.

## 🚀 Quick Start
1. Clone the repo.
2. `cp .env.example .env` and fill in your API keys.
3. Run `docker-compose up --build`.
4. Index the knowledge base: `docker-compose exec api python app/services/ingestion.py`.
