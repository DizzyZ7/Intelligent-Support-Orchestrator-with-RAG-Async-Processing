from pathlib import Path


def test_application_entrypoint_exists():
    root = Path(__file__).resolve().parents[1]
    assert (root / 'app/api/routes.py').is_file()
    assert (root / 'app/worker/tasks.py').is_file()
