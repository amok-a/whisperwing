import logging
import queue
import threading

import numpy as np
from faster_whisper import WhisperModel

from . import config
from .conversation_buffer import ConversationBuffer

logger = logging.getLogger(__name__)


def load_whisper_model():
    return WhisperModel(config.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")


def transcriber_thread(
    model,
    speech_queue: queue.Queue,
    stop_event: threading.Event,
    buffer: ConversationBuffer,
    signals,
):
    while not stop_event.is_set():
        try:
            audio_bytes = speech_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        try:
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0

            segments, info = model.transcribe(
                audio_np,
                language=config.WHISPER_LANGUAGE,
                condition_on_previous_text=False,
                initial_prompt=config.WHISPER_INITIAL_PROMPT,
            )
            text = " ".join(seg.text for seg in segments).strip()

            if text:
                logger.info(f">> {text}")
                buffer.append(text)
                signals.transcript_line.emit(text)
        except Exception:
            logger.exception("Ошибка в обработке сегмента речи")
