"""Redis-backed deduplication for support ticket drafts.

Keys are scoped to the ticket and exact question content. A lease prevents
concurrent workers from publishing the same draft. Completion is recorded
only after Zendesk confirms the update.
"""
import hashlib
import uuid

from redis import Redis
from app.core.config import settings

LEASE_SECONDS = 600
COMPLETED_SECONDS = 7 * 24 * 3600
_RELEASE = """if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"""
_COMPLETE = """if redis.call('get', KEYS[1]) == ARGV[1] then redis.call('set', KEYS[2], '1', 'EX', ARGV[2]); return redis.call('del', KEYS[1]) else return 0 end"""


class TicketLease:
    def __init__(self, ticket_id: int, question: str):
        digest = hashlib.sha256(f"{ticket_id}:{question}".encode("utf-8")).hexdigest()
        self.lock_key = f"support:lock:{digest}"
        self.done_key = f"support:done:{digest}"
        self.token = uuid.uuid4().hex
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

    def acquire(self) -> str:
        if self.redis.exists(self.done_key):
            return "completed"
        if not self.redis.set(self.lock_key, self.token, nx=True, ex=LEASE_SECONDS):
            return "busy"
        # Close race between the first completion check and lock acquisition.
        if self.redis.exists(self.done_key):
            self.release()
            return "completed"
        return "acquired"

    def complete(self) -> None:
        if not self.redis.eval(_COMPLETE, 2, self.lock_key, self.done_key, self.token, COMPLETED_SECONDS):
            raise RuntimeError("Ticket lease expired before completion was recorded")

    def release(self) -> None:
        self.redis.eval(_RELEASE, 1, self.lock_key, self.token)
