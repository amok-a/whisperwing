import sys
import queue
import threading

import pyaudiowpatch as pyaudio
from PyQt6.QtWidgets import QApplication

from . import config
from . import actions
from .audio_capture import find_loopback_device, recorder_thread
from .vad_segmenter import segmenter_thread
from .transcriber import load_whisper_model, transcriber_thread
from .conversation_buffer import ConversationBuffer
from .llm.factory import get_llm_client
from .signals import Signals
from .overlay import OverlayWindow
from .hotkeys import register_hotkeys


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

    raw_queue = queue.Queue()
    speech_queue = queue.Queue()
    stop_event = threading.Event()
    listening_event = threading.Event()
    if config.LISTEN_ON_START:
        listening_event.set()
    buffer = ConversationBuffer()

    app = QApplication(sys.argv)
    signals = Signals()

    def on_toggle_listen():
        actions.toggle_listening(listening_event, buffer, signals)

    def on_explain():
        threading.Thread(
            target=actions.explain_transcript, args=(buffer, llm_client, signals), daemon=True
        ).start()

    def on_explain_screen():
        threading.Thread(
            target=actions.explain_screen, args=(buffer, llm_client, signals), daemon=True
        ).start()

    window = OverlayWindow(signals, on_toggle_listen, on_explain, on_explain_screen)
    window.closing.connect(stop_event.set)
    window.show()

    register_hotkeys(buffer, llm_client, listening_event, signals)

    rec_thread = threading.Thread(
        target=recorder_thread,
        args=(device, rate, channels, raw_queue, stop_event, listening_event),
        daemon=True,
    )
    seg_thread = threading.Thread(
        target=segmenter_thread,
        args=(rate, channels, raw_queue, speech_queue, stop_event),
        daemon=True,
    )
    trans_thread = threading.Thread(
        target=transcriber_thread,
        args=(model, speech_queue, stop_event, buffer, signals),
        daemon=True,
    )

    rec_thread.start()
    seg_thread.start()
    trans_thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
