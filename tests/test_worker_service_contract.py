from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_worker_dependencies_present():
    assert (ROOT / "app/services/llm_service.py").is_file()
    assert (ROOT / "app/services/zendesk.py").is_file()


def test_zendesk_notes_private():
    code = (ROOT / "app/services/zendesk.py").read_text(encoding="utf-8")
    assert '"public": False' in code
