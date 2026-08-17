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

# VAD (Voice Activity Detection) — нарезка речи по паузам, а не по фиксированному времени
VAD_AGGRESSIVENESS = 2         # 0 (мягкий) — 3 (жёстко отсекает тишину/шум)
VAD_SILENCE_MS = 600           # тишина такой длины считается концом фразы
VAD_MIN_SEGMENT_SECONDS = 0.5  # короче — считаем шумом, выбрасываем
VAD_MAX_SEGMENT_SECONDS = 20   # длиннее — режем принудительно (говорят без пауз)

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