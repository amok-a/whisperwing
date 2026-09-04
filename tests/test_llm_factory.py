import pytest

from src import config
from src.llm.factory import get_llm_client
from src.llm.ollama_client import OllamaLLMClient
from src.llm.anthropic_client import AnthropicLLMClient


def test_ollama_provider_returns_ollama_client(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "ollama")
    client = get_llm_client()
    assert isinstance(client, OllamaLLMClient)


def test_anthropic_provider_without_key_raises(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", None)

    with pytest.raises(RuntimeError):
        get_llm_client()


def test_anthropic_provider_with_key_returns_anthropic_client(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "dummy-key-for-test")

    client = get_llm_client()
    assert isinstance(client, AnthropicLLMClient)


def test_unknown_provider_raises_value_error(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "not-a-real-provider")

    with pytest.raises(ValueError):
        get_llm_client()