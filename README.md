# Intelligent Support Orchestrator

Production-oriented support automation service that uses **RAG (Retrieval-Augmented Generation)** to answer customer requests from an internal knowledge base.

The project separates synchronous API handling from resource-intensive LLM and retrieval work. FastAPI accepts requests, Celery moves processing to background workers, Redis acts as the task broker, and Qdrant stores vector representations of internal documents.

## What the project demonstrates

- asynchronous processing of support requests;
- document ingestion and semantic retrieval;
- RAG-based answers grounded in internal documentation;
- separation of API and worker workloads;
- reproducible local deployment with Docker Compose;
- a practical foundation for CRM, helpdesk and internal knowledge-base integrations.

## Architecture

```text
Client / Helpdesk
        |
        v
 FastAPI service
        |
        v
 Redis task broker ---> Celery worker
                            |
                            +----> LangChain / LLM pipeline
                            |
                            +----> Qdrant vector search
                                        |
                                        v
                              Internal knowledge base
```

## Tech stack

- **Python / FastAPI** — asynchronous API layer;
- **Celery** — background task execution;
- **Redis** — Celery broker and task transport;
- **Qdrant** — vector database for semantic search;
- **LangChain** — RAG pipeline orchestration;
- **Docker / Docker Compose** — local deployment and service isolation.

## Quick start

### 1. Prepare environment

```bash
git clone https://github.com/DizzyZ7/Intelligent-Support-Orchestrator-with-RAG-Async-Processing.git
cd Intelligent-Support-Orchestrator-with-RAG-Async-Processing
cp .env.example .env
```

Fill in the required values in `.env`.

### 2. Start the stack

```bash
docker compose up --build
```

The Compose stack starts:

- FastAPI service on port `8000`;
- Celery worker;
- Redis on port `6379`;
- Qdrant on port `6333` with persistent local storage.

### 3. Index the knowledge base

```bash
docker compose exec api python app/services/ingestion.py
```

## Typical use cases

- first-line support assistant;
- internal employee knowledge base;
- helpdesk ticket classification and draft generation;
- answers based on product or operational documentation;
- retrieval layer for CRM and support automation.

## Engineering focus

This repository focuses on the backend architecture around an LLM rather than a simple prompt wrapper: asynchronous execution, vector retrieval, document ingestion, isolated services and repeatable deployment.

## Author

**Dimash Janibekov**  
Python Backend / Integration & Automation Engineer

- GitHub: [DizzyZ7](https://github.com/DizzyZ7)
- Telegram: [@dizzy_dev](https://t.me/dizzy_dev)
- Portfolio: [DizZy Systems Atlas](https://dizzyz7.github.io/DizZy-Systems-Atlas/)