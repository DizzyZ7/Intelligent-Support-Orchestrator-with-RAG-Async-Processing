"""Zendesk internal-note adapter. Does not publish customer-visible replies."""
import httpx
from app.core.config import settings


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
