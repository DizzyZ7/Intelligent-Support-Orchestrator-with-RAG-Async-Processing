"""Runtime integration tests with isolated external services and no real credentials."""
import os
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-placeholder")
os.environ.setdefault("ZENDESK_API_TOKEN", "test-placeholder")
os.environ.setdefault("ZENDESK_SUBDOMAIN", "example")
os.environ.setdefault("ZENDESK_EMAIL", "test@example.invalid")
os.environ.setdefault("WEBHOOK_SECRET", "test-secret")


def test_webhook_rejects_unauthorized_without_enqueuing(monkeypatch):
    from fastapi.testclient import TestClient
    from app.api import routes

    enqueue = Mock()
    monkeypatch.setattr(routes.process_ticket_task, "delay", enqueue)
    client = TestClient(routes.app)
    payload = {"ticket_id": 42, "subject": "Help", "description": "Question", "customer_email": "a@example.invalid"}
    assert client.post("/webhook/ticket", json=payload).status_code == 401
    assert client.post("/webhook/ticket", json=payload, headers={"X-Webhook-Secret": "wrong"}).status_code == 401
    enqueue.assert_not_called()


def test_webhook_queues_only_authorized_request(monkeypatch):
    from fastapi.testclient import TestClient
    from app.api import routes

    enqueue = Mock(return_value=SimpleNamespace(id="task-123"))
    monkeypatch.setattr(routes.process_ticket_task, "delay", enqueue)
    response = TestClient(routes.app).post("/webhook/ticket", json={
        "ticket_id": 42, "subject": "Help", "description": "Question", "customer_email": "a@example.invalid",
    }, headers={"X-Webhook-Secret": "test-secret"})
    assert response.status_code == 200
    assert response.json() == {"status": "accepted", "ticket_id": 42, "task_id": "task-123"}
    enqueue.assert_called_once_with(ticket_id=42, user_query="Question")


def test_webhook_queue_failure_is_not_leaked(monkeypatch):
    from fastapi.testclient import TestClient
    from app.api import routes

    monkeypatch.setattr(routes.process_ticket_task, "delay", Mock(side_effect=RuntimeError("broker-password")))
    response = TestClient(routes.app).post("/webhook/ticket", json={
        "ticket_id": 42, "subject": "Help", "description": "Question", "customer_email": "a@example.invalid",
    }, headers={"X-Webhook-Secret": "test-secret"})
    assert response.status_code == 500
    assert "broker-password" not in response.text


def test_zendesk_posts_private_note_and_checks_response(monkeypatch):
    from app.services import zendesk

    response = Mock()
    client = Mock()
    client.put.return_value = response
    manager = Mock()
    manager.__enter__ = Mock(return_value=client)
    manager.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(zendesk.httpx, "Client", Mock(return_value=manager))
    zendesk.post_comment_to_ticket(42, "Draft with [1] citation")
    kwargs = client.put.call_args.kwargs
    assert kwargs["json"] == {"ticket": {"comment": {"body": "Draft with [1] citation", "public": False}}}
    assert kwargs["auth"][0].endswith("/token")
    response.raise_for_status.assert_called_once()


def test_zendesk_rejects_invalid_note_without_network(monkeypatch):
    from app.services import zendesk

    client = Mock()
    monkeypatch.setattr(zendesk.httpx, "Client", client)
    with pytest.raises(ValueError):
        zendesk.post_comment_to_ticket(0, "Draft")
    with pytest.raises(ValueError):
        zendesk.post_comment_to_ticket(42, "   ")
    client.assert_not_called()


def test_rag_no_evidence_never_invokes_chat_model(monkeypatch):
    from app.services import llm_service

    store = Mock()
    store.similarity_search.return_value = []
    monkeypatch.setattr(llm_service, "QdrantClient", Mock())
    monkeypatch.setattr(llm_service, "OpenAIEmbeddings", Mock())
    monkeypatch.setattr(llm_service, "Qdrant", Mock(return_value=store))
    model = Mock()
    monkeypatch.setattr(llm_service, "ChatOpenAI", model)
    assert "Human review required" in llm_service.generate_rag_answer("Where is my order?")
    model.assert_not_called()
    store.similarity_search.assert_called_once_with("Where is my order?", k=4)


def test_worker_calls_rag_then_private_note(monkeypatch):
    from app.worker import tasks

    lease = Mock() 
    lease.acquire.return_value = "acquired"
    monkeypatch.setattr(tasks, "TicketLease", Mock(return_value=lease))
    monkeypatch.setattr(tasks, "note_exists", Mock(return_value=False))
    monkeypatch.setattr(tasks, "note_marker", Mock(return_value="[marker]"))
    rag = Mock(return_value="Internal draft")
    note = Mock()
    monkeypatch.setattr(tasks, "generate_rag_answer", rag)
    monkeypatch.setattr(tasks, "post_comment_to_ticket", note)
    result = tasks.process_ticket_task.run(ticket_id=42, user_query="Question")
    assert result == {"status": "success", "ticket_id": 42}
    rag.assert_called_once_with("Question")
    note.assert_called_once_with(42, "Internal draft\\n\\n[marker]")
    lease.complete.assert_called_once()


def test_worker_skips_completed_ticket(monkeypatch):
    from app.worker import tasks

    lease = Mock()
    lease.acquire.return_value = "completed"
    monkeypatch.setattr(tasks, "TicketLease", Mock(return_value=lease))
    rag = Mock()
    note = Mock()
    monkeypatch.setattr(tasks, "generate_rag_answer", rag)
    monkeypatch.setattr(tasks, "post_comment_to_ticket", note)
    assert tasks.process_ticket_task.run(42, "Question")["status"] == "already_processed"
    rag.assert_not_called()
    note.assert_not_called()


def test_worker_skips_concurrent_ticket(monkeypatch):
    from app.worker import tasks

    lease = Mock()
    lease.acquire.return_value = "busy"
    monkeypatch.setattr(tasks, "TicketLease", Mock(return_value=lease))
    note = Mock()
    monkeypatch.setattr(tasks, "post_comment_to_ticket", note)
    assert tasks.process_ticket_task.run(42, "Question")["status"] == "in_progress"
    note.assert_not_called()



def test_worker_reconciles_existing_zendesk_note(monkeypatch):
    from app.worker import tasks

    lease = Mock()
    lease.acquire.return_value = "acquired"
    monkeypatch.setattr(tasks, "TicketLease", Mock(return_value=lease))
    monkeypatch.setattr(tasks, "note_marker", Mock(return_value="[marker]"))
    monkeypatch.setattr(tasks, "note_exists", Mock(return_value=True))
    rag = Mock()
    note = Mock()
    monkeypatch.setattr(tasks, "generate_rag_answer", rag)
    monkeypatch.setattr(tasks, "post_comment_to_ticket", note)
    assert tasks.process_ticket_task.run(42, "Question")["status"] == "already_processed"
    rag.assert_not_called()
    note.assert_not_called()
    lease.complete.assert_called_once()


def test_zendesk_remote_marker_search(monkeypatch):
    from app.services import zendesk

    response = Mock()
    response.json.return_value = {"comments": [{"public": False, "body": "Draft\\n[marker]"}], "next_page": None}
    client = Mock()
    client.get.return_value = response
    manager = Mock()
    manager.__enter__ = Mock(return_value=client)
    manager.__exit__ = Mock(return_value=False)
    monkeypatch.setattr(zendesk.httpx, "Client", Mock(return_value=manager))
    assert zendesk.note_exists(42, "[marker]") is True
    response.raise_for_status.assert_called_once()


def test_worker_does_not_retry_permanent_http_error(monkeypatch):
    import httpx
    from app.worker import tasks

    lease = Mock()
    lease.acquire.return_value = "acquired"
    monkeypatch.setattr(tasks, "TicketLease", Mock(return_value=lease))
    monkeypatch.setattr(tasks, "note_marker", Mock(return_value="[marker]"))
    request = httpx.Request("GET", "https://example.zendesk.com/api/v2/tickets/42/comments.json")
    response = httpx.Response(403, request=request)
    failure = httpx.HTTPStatusError("Forbidden", request=request, response=response)
    monkeypatch.setattr(tasks, "note_exists", Mock(side_effect=failure))
    retry = Mock(side_effect=AssertionError("permanent error must not retry"))
    monkeypatch.setattr(tasks.process_ticket_task, "retry", retry)
    with pytest.raises(httpx.HTTPStatusError):
        tasks.process_ticket_task.run(42, "Question")
    lease.release.assert_called_once()
    retry.assert_not_called()


def test_worker_retries_temporary_http_error(monkeypatch):
    import httpx
    from app.worker import tasks

    lease = Mock()
    lease.acquire.return_value = "acquired"
    monkeypatch.setattr(tasks, "TicketLease", Mock(return_value=lease))
    monkeypatch.setattr(tasks, "note_marker", Mock(return_value="[marker]"))
    request = httpx.Request("GET", "https://example.zendesk.com/api/v2/tickets/42/comments.json")
    response = httpx.Response(503, request=request)
    failure = httpx.HTTPStatusError("Unavailable", request=request, response=response)
    monkeypatch.setattr(tasks, "note_exists", Mock(side_effect=failure))
    retry = Mock(side_effect=RuntimeError("retry scheduled"))
    monkeypatch.setattr(tasks.process_ticket_task, "retry", retry)
    with pytest.raises(RuntimeError, match="retry scheduled"):
        tasks.process_ticket_task.run(42, "Question")
    lease.release.assert_called_once()
    retry.assert_called_once()
