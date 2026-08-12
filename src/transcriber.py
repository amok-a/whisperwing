import numpy as np
import queue
import threading
import traceback
from faster_whisper import WhisperModel

from . import config
from .audio_capture import resample_audio_bytes, save_debug_wav
from .conversation_buffer import ConversationBuffer


def load_whisper_model():
    return WhisperModel(config.WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")


def transcriber_thread(
    model,
    rate,
    channels,
    audio_queue: queue.Queue,
    stop_event: threading.Event,
    buffer: ConversationBuffer,
):
    chunk_counter = 0

    while not stop_event.is_set():
        try:
            audio_bytes = audio_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        chunk_counter += 1

        try:
            if config.SAVE_DEBUG_CHUNKS:
                save_debug_wav(audio_bytes, rate, channels, f"debug_chunk_{chunk_counter}.wav")

            audio_bytes_16k = resample_audio_bytes(audio_bytes, rate, channels)
            audio_np = np.frombuffer(audio_bytes_16k, dtype=np.int16).astype(np.float32) / 32768.0
            if channels > 1:
                audio_np = audio_np.reshape(-1, channels).mean(axis=1)

            rms = np.sqrt(np.mean(audio_np ** 2))
            if rms < config.SILENCE_RMS_THRESHOLD:
                continue

            segments, info = model.transcribe(
                audio_np,
                language=config.WHISPER_LANGUAGE,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                condition_on_previous_text=False,
            )
            text = " ".join(seg.text for seg in segments).strip()

            if text:
                print(f">> {text}")
                buffer.append(text)
        except Exception:
            print(f"Ошибка в обработке чанка {chunk_counter}:")
            traceback.print_exc()
