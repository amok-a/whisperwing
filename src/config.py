from typing import Literal, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Whisper
    WHISPER_MODEL_SIZE: str = "base"
    WHISPER_LANGUAGE: str = "ru"
    WHISPER_INITIAL_PROMPT: str = (
        "Технический созвон разработчиков. Встречаются термины: "
        "HTTP, HTTPS, API, JSON, SQL, REST, backend, frontend, database, "
        "Python, Docker, Kubernetes, инкапсуляция, полиморфизм, наследование."
    )

    # Аудио
    TARGET_SAMPLE_RATE: int = 16000

    # VAD (Silero)
    VAD_THRESHOLD: float = Field(default=0.5, ge=0.0, le=1.0)
    VAD_SPEECH_PAD_MS: int = Field(default=30, ge=0)
    VAD_SILENCE_MS: int = Field(default=600, ge=0)
    VAD_MIN_SEGMENT_SECONDS: float = Field(default=0.5, ge=0.0)
    VAD_MAX_SEGMENT_SECONDS: float = Field(default=20.0, gt=0.0)

    # Буфер разговора
    BUFFER_MINUTES: int = Field(default=5, gt=0)

    # Хоткеи
    EXPLAIN_HOTKEY: str = "ctrl+shift+e"
    LISTEN_TOGGLE_HOTKEY: str = "ctrl+shift+l"
    SCREEN_HOTKEY: str = "ctrl+shift+s"
    LISTEN_ON_START: bool = False

    # LLM-провайдер
    LLM_PROVIDER: Literal["ollama", "anthropic"] = "ollama"

    # Anthropic
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-sonnet-5"

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b"
    OLLAMA_VISION_MODEL: str = "llava:7b"

    @model_validator(mode="after")
    def check_anthropic_key_present(self) -> "Settings":
        if self.LLM_PROVIDER == "anthropic" and not self.ANTHROPIC_API_KEY:
            raise ValueError(
                "LLM_PROVIDER=anthropic требует заполненный ANTHROPIC_API_KEY в .env"
            )
        return self


settings = Settings()

# Плоские модульные переменные для обратной совместимости — остальной код
# обращается к ним как config.WHISPER_MODEL_SIZE и т.д., менять его не нужно.
WHISPER_MODEL_SIZE = settings.WHISPER_MODEL_SIZE
WHISPER_LANGUAGE = settings.WHISPER_LANGUAGE
WHISPER_INITIAL_PROMPT = settings.WHISPER_INITIAL_PROMPT

TARGET_SAMPLE_RATE = settings.TARGET_SAMPLE_RATE

VAD_THRESHOLD = settings.VAD_THRESHOLD
VAD_SPEECH_PAD_MS = settings.VAD_SPEECH_PAD_MS
VAD_SILENCE_MS = settings.VAD_SILENCE_MS
VAD_MIN_SEGMENT_SECONDS = settings.VAD_MIN_SEGMENT_SECONDS
VAD_MAX_SEGMENT_SECONDS = settings.VAD_MAX_SEGMENT_SECONDS

BUFFER_MINUTES = settings.BUFFER_MINUTES

EXPLAIN_HOTKEY = settings.EXPLAIN_HOTKEY
LISTEN_TOGGLE_HOTKEY = settings.LISTEN_TOGGLE_HOTKEY
SCREEN_HOTKEY = settings.SCREEN_HOTKEY
LISTEN_ON_START = settings.LISTEN_ON_START

LLM_PROVIDER = settings.LLM_PROVIDER

ANTHROPIC_API_KEY = settings.ANTHROPIC_API_KEY
ANTHROPIC_MODEL = settings.ANTHROPIC_MODEL

OLLAMA_BASE_URL = settings.OLLAMA_BASE_URL
OLLAMA_MODEL = settings.OLLAMA_MODEL
OLLAMA_VISION_MODEL = settings.OLLAMA_VISION_MODEL
