from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from app.worker.tasks import process_ticket_task
import logging
import hmac
from fastapi import Header
from app.core.config import settings

# Настройка логов
logger = logging.getLogger(__name__)

app = FastAPI(title="Support Orchestrator API")

# Схема входящих данных (например, для Zendesk/Usedesk)
class TicketWebhook(BaseModel):
    ticket_id: int
    subject: str
    description: str
    customer_email: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/webhook/ticket")
async def handle_new_ticket(payload: TicketWebhook, x_webhook_secret: str | None = Header(default=None)):
    if not x_webhook_secret or not hmac.compare_digest(x_webhook_secret, settings.WEBHOOK_SECRET):
        raise HTTPException(status_code=401, detail="Unauthorized")
    """
    Эндпоинт для приема вебхуков. 
    Мы не обрабатываем логику тут, а кидаем задачу в Celery.
    """
    try:
        # Отправляем задачу в очередь Redis
        task = process_ticket_task.delay(
            ticket_id=payload.ticket_id,
            user_query=payload.description
        )
        
        logger.info(f"Ticket {payload.ticket_id} queued with task_id {task.id}")
        
        return {
            "status": "accepted",
            "ticket_id": payload.ticket_id,
            "task_id": task.id
        }
    except Exception as e:
        logger.error(f"Failed to queue ticket {payload.ticket_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Queue Error")
