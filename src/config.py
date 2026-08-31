import os
from dotenv import load_dotenv

load_dotenv()

# Whisper
WHISPER_MODEL_SIZE = "base"
WHISPER_LANGUAGE = "ru"
WHISPER_INITIAL_PROMPT = (
    "Технический созвон разработчиков. Встречаются термины: "
    "HTTP, HTTPS, API, JSON, SQL, REST, backend, frontend, database, "
    "Python, Docker, Kubernetes, инкапсуляция, полиморфизм, наследование."
)

# Аудио
TARGET_SAMPLE_RATE = 16000

VAD_THRESHOLD = 0.5        # порог уверенности модели, что это речь (0-1)
VAD_SPEECH_PAD_MS = 30      # небольшой запас звука до/после речи, чтобы не резать края слов
VAD_SILENCE_MS = 600
VAD_MIN_SEGMENT_SECONDS = 0.5
VAD_MAX_SEGMENT_SECONDS = 20

# Буфер разговора
BUFFER_MINUTES = 5

# Хоткей
EXPLAIN_HOTKEY = "ctrl+shift+e"

# LLM-провайдер: "ollama" или "anthropic"
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama")

# Anthropic
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = "claude-sonnet-5"

# Ollama
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")

# Старт/стоп прослушивания
LISTEN_TOGGLE_HOTKEY = "ctrl+shift+l"
LISTEN_ON_START = False  # запускать ли прослушивание сразу при старте скрипта

# Захват экрана
SCREEN_HOTKEY = "ctrl+shift+s"

# Ollama vision-модель (отдельно от текстовой)
OLLAMA_VISION_MODEL = os.environ.get("OLLAMA_VISION_MODEL", "llava:7b")