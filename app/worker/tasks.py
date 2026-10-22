"""Asynchronous support-ticket processing with Redis deduplication."""
import logging

from app.core.celery_app import celery_app
from app.services.idempotency import TicketLease
from app.services.llm_service import generate_rag_answer
from app.services.zendesk import post_comment_to_ticket

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
            raise self.retry(countdown=30)
        try:
            answer = generate_rag_answer(user_query)
            post_comment_to_ticket(ticket_id, answer)
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
