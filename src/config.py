import os
from dotenv import load_dotenv

load_dotenv()

# Захват аудио
CHUNK_SECONDS = 8
TARGET_SAMPLE_RATE = 16000
SILENCE_RMS_THRESHOLD = 0.01
SAVE_DEBUG_CHUNKS = False

# Whisper
WHISPER_MODEL_SIZE = "base"
WHISPER_LANGUAGE = "ru"

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
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b")
