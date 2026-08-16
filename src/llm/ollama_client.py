import requests

from .. import config
from .base import LLMClient, EXPLAIN_SYSTEM_PROMPT


class OllamaLLMClient(LLMClient):
    def __init__(self):
        self._base_url = config.OLLAMA_BASE_URL
        self._model = config.OLLAMA_MODEL

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
