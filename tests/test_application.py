import threading

import pytest

import src.application as app_module
from src.application import Application


class FakeLLMClient:
    def explain(self, transcript: str) -> str:
        return "ok"

    def explain_image(self, image_bytes: bytes, context: str) -> str:
        return "ok"


class FakeSignals:
    pass


@pytest.fixture
def patched_app(monkeypatch):
    """Подменяет всё, что требует реального железа и моделей, на заглушки,
    чтобы проверить именно логику жизненного цикла."""
    monkeypatch.setattr(app_module, "load_whisper_model", lambda: object())

    class FakePyAudio:
        def terminate(self):
            pass

    monkeypatch.setattr(app_module.pyaudio, "PyAudio", FakePyAudio)
    monkeypatch.setattr(
        app_module,
        "find_loopback_device",
        lambda p: {"name": "fake", "defaultSampleRate": 48000, "maxInputChannels": 2, "index": 0},
    )

    def fake_worker(*args, **kwargs):
        # Ищем stop_event среди аргументов и ждём сигнала остановки,
        # имитируя поведение настоящего рабочего потока.
        for arg in args:
            if isinstance(arg, threading.Event):
                while not arg.is_set():
                    arg.wait(0.05)
                return

    monkeypatch.setattr(app_module, "recorder_thread", fake_worker)
    monkeypatch.setattr(app_module, "segmenter_thread", fake_worker)
    monkeypatch.setattr(app_module, "transcriber_thread", fake_worker)

    return Application(FakeLLMClient(), FakeSignals())


def test_start_without_prepare_raises(patched_app):
    with pytest.raises(RuntimeError):
        patched_app.start()


def test_start_launches_three_threads(patched_app):
    patched_app.prepare()
    patched_app.start()

    try:
        assert len(patched_app._threads) == 3
        assert all(t.is_alive() for t in patched_app._threads)
    finally:
        patched_app.stop()


def test_stop_joins_all_threads(patched_app):
    patched_app.prepare()
    patched_app.start()
    threads = list(patched_app._threads)

    patched_app.stop()

    assert all(not t.is_alive() for t in threads)
    assert patched_app._threads == []


def test_double_start_is_ignored(patched_app):
    patched_app.prepare()
    patched_app.start()

    try:
        first_threads = list(patched_app._threads)
        patched_app.start()
        assert patched_app._threads == first_threads
    finally:
        patched_app.stop()


def test_stop_without_start_is_safe(patched_app):
    patched_app.stop()


def test_context_manager_starts_and_stops(patched_app):
    with patched_app as app:
        assert len(app._threads) == 3

    assert patched_app._threads == []