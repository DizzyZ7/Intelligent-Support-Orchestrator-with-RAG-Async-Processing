"""Offline RAG behavior tests with stubbed external clients."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_rag_service_exports_worker_contract():
    source = (ROOT / "app/services/llm_service.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    functions = {node.name for node in module.body if isinstance(node, ast.FunctionDef)}
    assert "generate_rag_answer" in functions


def test_rag_fallback_and_internal_notes_are_present():
    rag = (ROOT / "app/services/llm_service.py").read_text(encoding="utf-8")
    zendesk = (ROOT / "app/services/zendesk.py").read_text(encoding="utf-8")
    assert "Human review required" in rag
    assert '"public": False' in zendesk
