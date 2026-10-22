from pathlib import Path

def test_no_destructive_recreation():
    source = (Path(__file__).resolve().parents[1] / 'app/services/ingestion.py').read_text()
    assert 'force_recreate=True' not in source
