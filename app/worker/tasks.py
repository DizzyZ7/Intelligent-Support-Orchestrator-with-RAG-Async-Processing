from app.core.celery_app import celery_app
from app.services.llm_service import generate_rag_answer
from app.services.zendesk import post_comment_to_ticket
import logging

logger = logging.getLogger(__name__)

@celery_app.task(name="process_support_ticket", bind=True, max_retries=3)
def process_ticket_task(self, ticket_id: int, user_query: str):
    try:
        logger.info(f"Processing ticket {ticket_id}")
        
        # 1. Получаем ответ от RAG системы
        answer = generate_rag_answer(user_query)
        
        # 2. Отправляем ответ обратно в Usedesk/Zendesk как внутреннюю заметку
        post_comment_to_ticket(ticket_id, answer)
        
        return {"status": "success", "ticket_id": ticket_id}
    except Exception as exc:
        logger.error(f"Error processing ticket {ticket_id}: {exc}")
        # Ретрай при ошибках сети или API
        raise self.retry(exc=exc, countdown=60)
