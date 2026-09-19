import logging
import threading

import pyaudiowpatch as pyaudio

from . import config
from .audio_capture import find_loopback_device, recorder_thread
from .bounded_queue import DropOldestQueue
from .conversation_buffer import ConversationBuffer
from .llm.base import LLMClient
from .signals import Signals
from .transcriber import load_whisper_model, transcriber_thread
from .vad_segmenter import segmenter_thread

logger = logging.getLogger(__name__)

THREAD_JOIN_TIMEOUT = 5.0


class Application:
    """Владеет жизненным циклом аудио-пайплайна: подготовка ресурсов,
    запуск рабочих потоков и упорядоченная остановка."""

    def __init__(self, llm_client: LLMClient, signals: Signals) -> None:
        self._llm_client = llm_client
        self._signals = signals

        self._stop_event = threading.Event()
        self._listening_event = threading.Event()
        if config.LISTEN_ON_START:
            self._listening_event.set()

        self.buffer = ConversationBuffer()

        self._raw_queue = DropOldestQueue(maxsize=config.RAW_QUEUE_MAXSIZE, name="raw_queue")
        self._speech_queue = DropOldestQueue(
            maxsize=config.SPEECH_QUEUE_MAXSIZE, name="speech_queue"
        )

        self._threads: list[threading.Thread] = []
        self._model = None
        self._device: dict | None = None
        self._rate: int | None = None
        self._channels: int | None = None
        self._started = False

    @property
    def listening_event(self) -> threading.Event:
        return self._listening_event

    def prepare(self) -> None:
        """Обнаруживает аудиоустройство и загружает модель распознавания.
        Вынесено из start(), чтобы долгая загрузка модели произошла до
        показа UI, а не в момент, когда пользователь уже нажимает кнопки."""
        p = pyaudio.PyAudio()
        try:
            self._device = find_loopback_device(p)
            self._rate = int(self._device["defaultSampleRate"])
            self._channels = int(self._device["maxInputChannels"])
        finally:
            p.terminate()

        logger.info(
            f"Устройство: {self._device['name']}, rate={self._rate}, channels={self._channels}"
        )
        logger.info(f"LLM-провайдер: {config.LLM_PROVIDER}")
        logger.info("Загружаю модель Whisper...")
        self._model = load_whisper_model()
        logger.info("Модель загружена.")

    def start(self) -> None:
        if self._started:
            logger.warning("Application.start() вызван повторно, игнорирую")
            return
        if self._model is None:
            raise RuntimeError("Нужно вызвать prepare() до start()")

        self._threads = [
            threading.Thread(
                target=recorder_thread,
                args=(
                    self._device,
                    self._rate,
                    self._channels,
                    self._raw_queue,
                    self._stop_event,
                    self._listening_event,
                ),
                name="recorder",
            ),
            threading.Thread(
                target=segmenter_thread,
                args=(
                    self._rate,
                    self._channels,
                    self._raw_queue,
                    self._speech_queue,
                    self._stop_event,
                ),
                name="segmenter",
            ),
            threading.Thread(
                target=transcriber_thread,
                args=(
                    self._model,
                    self._speech_queue,
                    self._stop_event,
                    self.buffer,
                    self._signals,
                ),
                name="transcriber",
            ),
        ]

        for thread in self._threads:
            thread.start()

        self._started = True
        logger.info("Пайплайн запущен")

    def stop(self) -> None:
        if not self._started:
            return

        logger.info("Останавливаю пайплайн...")
        self._listening_event.clear()
        self._stop_event.set()

        for thread in self._threads:
            thread.join(timeout=THREAD_JOIN_TIMEOUT)
            if thread.is_alive():
                logger.warning(
                    f"Поток {thread.name} не завершился за {THREAD_JOIN_TIMEOUT}с"
                )

        self._threads.clear()
        self._started = False

        dropped = self._raw_queue.dropped_count + self._speech_queue.dropped_count
        if dropped:
            logger.info(f"За сессию отброшено элементов из очередей: {dropped}")

        logger.info("Пайплайн остановлен")

    def __enter__(self) -> "Application":
        self.prepare()
        self.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.stop()
