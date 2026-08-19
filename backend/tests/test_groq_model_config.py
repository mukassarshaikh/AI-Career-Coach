"""
test_groq_model_config.py — Configuration test for Groq model selection.

Verifies that settings.groq_model resolves to 'openai/gpt-oss-120b'.
"""

from app.core.config import settings


def test_groq_model_configuration():
    """Verify that groq_model is configuration-driven and set to openai/gpt-oss-120b."""
    assert settings.groq_model == "openai/gpt-oss-120b"
