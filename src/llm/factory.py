from .. import config
from .base import LLMClient


def get_llm_client() -> LLMClient:
    if config.LLM_PROVIDER == "anthropic":
        from .anthropic_client import AnthropicLLMClient
        return AnthropicLLMClient()
    elif config.LLM_PROVIDER == "ollama":
        from .ollama_client import OllamaLLMClient
        return OllamaLLMClient()
    else:
        raise ValueError(f"Неизвестный LLM_PROVIDER: {config.LLM_PROVIDER}")
