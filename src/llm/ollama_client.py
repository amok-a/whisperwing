import base64
import requests

from .. import config
from .base import LLMClient, EXPLAIN_SYSTEM_PROMPT, IMAGE_EXPLAIN_SYSTEM_PROMPT


class OllamaLLMClient(LLMClient):
    def __init__(self):
        self._base_url = config.OLLAMA_BASE_URL
        self._model = config.OLLAMA_MODEL
        self._vision_model = config.OLLAMA_VISION_MODEL

    def explain(self, transcript: str) -> str:
        response = requests.post(
            f"{self._base_url}/api/chat",
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": EXPLAIN_SYSTEM_PROMPT},
                    {"role": "user", "content": transcript},
                ],
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]

    def explain_image(self, image_bytes: bytes, context: str) -> str:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        response = requests.post(
            f"{self._base_url}/api/chat",
            json={
                "model": self._vision_model,
                "messages": [
                    {"role": "system", "content": IMAGE_EXPLAIN_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": f"Контекст разговора (может быть пуст): {context}",
                        "images": [image_b64],
                    },
                ],
                "stream": False,
            },
            timeout=90,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]