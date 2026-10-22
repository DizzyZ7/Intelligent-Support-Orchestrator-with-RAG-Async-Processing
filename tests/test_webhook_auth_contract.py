from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_webhook_auth_guard_present():
    code = (ROOT / 'app/api/routes.py').read_text(encoding='utf-8')
    assert 'hmac.compare_digest' in code
    assert 'status_code=401' in code
    assert code.index('hmac.compare_digest') < code.index('process_ticket_task.delay')
