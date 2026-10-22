"""Asynchronous support-ticket processing with Redis deduplication."""
import logging

from app.core.celery_app import celery_app
from app.services.idempotency import TicketLease
from app.services.llm_service import generate_rag_answer
from app.services.zendesk import note_exists, note_marker, post_comment_to_ticket

logger = logging.getLogger(__name__)


@celery_app.task(name="process_support_ticket", bind=True, max_retries=3)
def process_ticket_task(self, ticket_id: int, user_query: str):
    lease = TicketLease(ticket_id, user_query)
    try:
        state = lease.acquire()
        if state == "completed":
            return {"status": "already_processed", "ticket_id": ticket_id}
        if state == "busy":
            # Another worker owns the lease. Retry rather than silently lose the job.
            return {"status": "in_progress", "ticket_id": ticket_id}
        try:
            marker = note_marker(ticket_id, user_query)
            if note_exists(ticket_id, marker):
                lease.complete()
                return {"status": "already_processed", "ticket_id": ticket_id}
            answer = generate_rag_answer(user_query)
            post_comment_to_ticket(ticket_id, f"{answer}\\n\\n{marker}")
            lease.complete()
            return {"status": "success", "ticket_id": ticket_id}
        except Exception:
            lease.release()
            raise
    except self.MaxRetriesExceededError:
        raise
    except Exception as exc:
        logger.exception("Ticket %s processing failed", ticket_id)
        raise self.retry(exc=exc, countdown=60)
