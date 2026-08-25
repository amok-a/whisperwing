import base64
from anthropic import Anthropic

from .. import config
from .base import LLMClient, EXPLAIN_SYSTEM_PROMPT, IMAGE_EXPLAIN_SYSTEM_PROMPT


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

    def explain_image(self, image_bytes: bytes, context: str) -> str:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": image_b64},
            },
            {
                "type": "text",
                "text": f"Контекст разговора (может быть пуст): {context}",
            },
        ]
        response = self._client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=400,
            system=IMAGE_EXPLAIN_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": content}],
        )
        return response.content[0].text