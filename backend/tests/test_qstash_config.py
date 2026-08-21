"""
test_qstash_config.py — Configuration test for Upstash QStash settings.

Verifies that qstash_url and qstash_token exist on Settings and resolve from environment variables QSTASH_URL and QSTASH_TOKEN.
"""

from app.core.config import Settings


def test_qstash_config_defaults():
    """Verify QStash configuration default attributes exist on Settings."""
    s = Settings()
    assert hasattr(s, "qstash_url")
    assert hasattr(s, "qstash_token")


def test_qstash_config_from_env(monkeypatch):
    """Verify QStash configuration fields correctly resolve from QSTASH_URL and QSTASH_TOKEN environment variables."""
    test_url = "https://qstash.upstash.io/v2/publish"
    test_token = "qstash_test_token_123"

    monkeypatch.setenv("QSTASH_URL", test_url)
    monkeypatch.setenv("QSTASH_TOKEN", test_token)

    s = Settings()
    assert s.qstash_url == test_url
    assert s.qstash_token == test_token
