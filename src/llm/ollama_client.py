import base64
import requests

from .. import config
from .base import LLMClient, EXPLAIN_SYSTEM_PROMPT, IMAGE_EXPLAIN_SYSTEM_PROMPT

IMAGE_DESCRIBE_PROMPT = (
    "Transcribe all text and code visible in this image as precisely "
    "as possible, verbatim where you can. Describe any diagrams, charts "
    "or UI elements. Be factual and thorough, do not add commentary or "
    "solve anything yourself."
)

IMAGE_TRANSLATE_SYSTEM_PROMPT = (
    "Тебе дано подробное описание/расшифровка скриншота (на английском) "
    "и, возможно, контекст разговора. Если в описании — вопрос, задача "
    "или проблема (например, задача по программированию) — реши её по "
    "существу и дай конкретный ответ или решение (с кодом, если уместно). "
    "Если это просто иллюстрация без явного вопроса — кратко объясни, что "
    "на ней и почему это может быть важно в контексте разговора, если "
    "контекст есть. Отвечай по-русски, без вступлений, без упоминания "
    "того, что тебе передали чьё-то описание."
)


class OllamaLLMClient(LLMClient):
    def __init__(self):
        self._base_url = config.OLLAMA_BASE_URL
        self._model = config.OLLAMA_MODEL
        self._vision_model = config.OLLAMA_VISION_MODEL

    def _chat(self, model: str, system: str, user_content, timeout=60) -> str:
        response = requests.post(
            f"{self._base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    user_content,
                ],
                "stream": False,
                "keep_alive": "30m",
                "options": {"num_predict": 300},
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def explain(self, transcript: str) -> str:
        return self._chat(
            self._model,
            EXPLAIN_SYSTEM_PROMPT,
            {"role": "user", "content": transcript},
        )

    def explain_image(self, image_bytes: bytes, context: str) -> str:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Шаг 1: llava просто описывает картинку, без задачи про язык/стиль
        description = self._chat(
            self._vision_model,
            "You are a precise image description assistant.",
            {
                "role": "user",
                "content": IMAGE_DESCRIBE_PROMPT,
                "images": [image_b64],
            },
            timeout=90,
        )

        # Шаг 2: текстовая модель оформляет описание как ответ на русском
        combined_input = (
            f"Описание скриншота: {description}\n\n"
            f"Контекст разговора (может быть пуст): {context}"
        )
        return self._chat(
            self._model,
            IMAGE_TRANSLATE_SYSTEM_PROMPT,
            {"role": "user", "content": combined_input},
        )