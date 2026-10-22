"""Zendesk internal-note adapter with remote duplicate reconciliation."""
import hashlib
import httpx
from app.core.config import settings


def note_marker(ticket_id: int, query: str) -> str:
    digest = hashlib.sha256(f"{ticket_id}:{query}".encode("utf-8")).hexdigest()
    return f"[support-orchestrator:{digest}]"


def note_exists(ticket_id: int, marker: str) -> bool:
    """Check all ticket comments before retrying a possibly completed PUT."""
    url = f"https://{settings.ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}/comments.json"
    auth = (f"{settings.ZENDESK_EMAIL}/token", settings.ZENDESK_API_TOKEN)
    with httpx.Client(timeout=15.0) as client:
        for _ in range(100):
            response = client.get(url, auth=auth)
            response.raise_for_status()
            payload = response.json()
            for comment in payload.get("comments", []):
                if comment.get("public") is False and marker in (comment.get("body") or ""):
                    return True
            next_page = payload.get("next_page")
            if not next_page:
                return False
            if not next_page.startswith(f"https://{settings.ZENDESK_SUBDOMAIN}.zendesk.com/"):
                raise ValueError("Unexpected Zendesk pagination URL")
            url = next_page
    raise RuntimeError("Zendesk comment pagination exceeded safety limit")


def post_comment_to_ticket(ticket_id: int, answer: str) -> None:
    if ticket_id <= 0:
        raise ValueError("ticket_id must be positive")
    if not answer.strip():
        raise ValueError("Refusing to post an empty note")
    url = f"https://{settings.ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/tickets/{ticket_id}.json"
    payload = {"ticket": {"comment": {"body": answer, "public": False}}}
    with httpx.Client(timeout=15.0) as client:
        response = client.put(
            url,
            json=payload,
            auth=(f"{settings.ZENDESK_EMAIL}/token", settings.ZENDESK_API_TOKEN),
        )
        response.raise_for_status()
