from anthropic import Anthropic

from .. import config
from .base import LLMClient, EXPLAIN_SYSTEM_PROMPT


class AnthropicLLMClient(LLMClient):
    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError("ANTHROPIC_API_KEY не найден. Проверь .env")
        self._client = Anthropic(api_key=config.ANTHROPIC_API_KEY)

    def explain(self, transcript: str) -> str:
        response = self._client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=400,
            system=EXPLAIN_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": transcript}],
        )
        return response.content[0].text
