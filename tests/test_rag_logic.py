import pytest
from app.services.llm_service import generate_answer

def test_answer_generation_with_context():
    question = "Как вернуть товар?"
    context = "Возврат товара возможен в течение 14 дней через личный кабинет."
    
    answer = generate_answer(question, context)
    
    assert "14 дней" in answer
    assert "личный кабинет" in answer
