# Initial architecture and security audit (Phase 0)

Date: 2026-10-23. Scope: targeted source review; **not** a complete repository audit or runtime validation.

## Verified architecture
- FastAPI API (Docker CMD: `app.api.routes:app`)
- Celery worker using Redis as broker and result backend (`app/core/celery_app.py`)
- Qdrant for vector storage; LangChain/OpenAI embeddings for ingestion (`app/services/ingestion.py`)
- Docker Compose orchestrates API, worker, Redis and Qdrant.

## Findings (evidence, severity, recommendation)

1. **P0 / High — destructive ingestion**: `app/services/ingestion.py` passes `force_recreate=True` to `QdrantVectorStore.from_documents` on the `support_kb` collection. Re-running ingestion can erase existing indexed documents. Replace with incremental, idempotent upserts and explicit versioned migration/rebuild procedures; test preservation of unrelated documents.
2. **P1 / High — infrastructure exposed by default**: `docker-compose.yml` publishes Redis `6379:6379` and Qdrant `6333:6333` on all interfaces by default. Remove public bindings for internal services or bind to loopback for development; implement authentication/network policy where applicable.
3. **P1 / High — development mounts in deployed API and worker**: `docker-compose.yml` bind-mounts `.:/app` into both containers. Separate dev/prod Compose configurations; production should use immutable images.
4. **P1 / Medium — debug defaults to enabled**: `app/core/config.py` declares `DEBUG: bool = True`. Default false; explicitly opt in for local development.
5. **P1 / Medium — unpinned service images**: `docker-compose.yml` uses `qdrant/qdrant` without a version and `redis:7-alpine` with a broad tag. Pin tested image versions or digests, and establish upgrade checks.

## Additional verification required
- Read `app/api/routes.py`, `app/worker/tasks.py`, `pyproject.toml`, tests and workflows.
- Validate webhook authentication, task retries, authorization and data flow.
- Run Docker Compose build, tests and ingestion against disposable data; none were executed in this audit.
- Check for secrets and unsafe logging without disclosing credentials.

## Prioritized roadmap
- **P0:** eliminate destructive collection recreation; add regression tests.
- **P1:** harden service exposure and production configuration; validate webhook auth and task resilience.
- **P2:** add retrieval quality benchmarks, cost metrics, integration adapters, observability.

## Product opportunities (proposals, not existing features)
1. Helpdesk connector with idempotent webhook processing and human approval.
2. Citation-grounded answer drafting with confidence thresholds.
3. Model routing and per-request cost accounting.

## Validation status
Static source inspection only. No claims of passing tests, successful Docker builds or production readiness.
