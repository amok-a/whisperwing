import queue
import threading
import time

import pyaudiowpatch as pyaudio

from . import config
from .audio_capture import find_loopback_device, recorder_thread
from .transcriber import load_whisper_model, transcriber_thread
from .conversation_buffer import ConversationBuffer
from .llm.factory import get_llm_client
from .hotkeys import register_explain_hotkey


def main():
    try:
        llm_client = get_llm_client()
    except Exception as e:
        print(f"Не удалось инициализировать LLM-клиента: {e}")
        return

    p = pyaudio.PyAudio()
    device = find_loopback_device(p)
    rate = int(device["defaultSampleRate"])
    channels = int(device["maxInputChannels"])
    p.terminate()

    print(f"Устройство: {device['name']}, rate={rate}, channels={channels}")
    print(f"LLM-провайдер: {config.LLM_PROVIDER}")
    print("Загружаю модель Whisper...")
    model = load_whisper_model()
    print("Модель загружена.")

    audio_queue = queue.Queue()
    stop_event = threading.Event()
    buffer = ConversationBuffer()

    register_explain_hotkey(buffer, llm_client)

    rec_thread = threading.Thread(
        target=recorder_thread, args=(device, rate, channels, audio_queue, stop_event)
    )
    trans_thread = threading.Thread(
        target=transcriber_thread,
        args=(model, rate, channels, audio_queue, stop_event, buffer),
    )

    rec_thread.start()
    trans_thread.start()

    print(f"Слушаю... ({config.EXPLAIN_HOTKEY} — объяснить, Ctrl+C — остановить)")

    try:
        while rec_thread.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nОстанавливаю...")
        stop_event.set()

    rec_thread.join(timeout=3)
    trans_thread.join(timeout=3)
    print("Остановлено.")


if __name__ == "__main__":
    main()
