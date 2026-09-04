import queue

import src.vad_segmenter as vad_module
from src.vad_segmenter import VadSegmenter, WINDOW_BYTES


class DummyVADIterator:

    def __init__(self, model, sampling_rate=None, threshold=None,
                 min_silence_duration_ms=None, speech_pad_ms=None):
        self.events = []

    def __call__(self, audio_tensor, return_seconds=False):
        if self.events:
            return self.events.pop(0)
        return None


def make_segmenter(monkeypatch, min_seconds=0.05, max_seconds=20.0):
    monkeypatch.setattr(vad_module, "load_silero_vad", lambda: object())
    monkeypatch.setattr(vad_module, "VADIterator", DummyVADIterator)
    monkeypatch.setattr(vad_module.config, "VAD_MIN_SEGMENT_SECONDS", min_seconds)
    monkeypatch.setattr(vad_module.config, "VAD_MAX_SEGMENT_SECONDS", max_seconds)

    segmenter = VadSegmenter(orig_rate=16000, channels=1)
    return segmenter


def _dummy_frame() -> bytes:
    return b"\x00\x01" * (WINDOW_BYTES // 2)


def test_segment_flushed_on_end_event(monkeypatch):
    segmenter = make_segmenter(monkeypatch, min_seconds=0.05)
    segmenter._vad_iterator.events = [{"start": 0}, None, None, {"end": 0}]

    out_queue = queue.Queue()
    for _ in range(4):
        segmenter._process_frame(_dummy_frame(), out_queue)

    assert out_queue.qsize() == 1
    segment = out_queue.get()
    assert len(segment) == 4 * WINDOW_BYTES


def test_short_segment_below_min_duration_is_discarded(monkeypatch):
    segmenter = make_segmenter(monkeypatch, min_seconds=1.0)  # заведомо больше, чем 2 кадра
    segmenter._vad_iterator.events = [{"start": 0}, {"end": 0}]

    out_queue = queue.Queue()
    segmenter._process_frame(_dummy_frame(), out_queue)
    segmenter._process_frame(_dummy_frame(), out_queue)

    assert out_queue.empty()


def test_segment_force_flushed_at_max_duration(monkeypatch):
    segmenter = make_segmenter(monkeypatch, min_seconds=0.0, max_seconds=0.05)
    segmenter._vad_iterator.events = [{"start": 0}]

    out_queue = queue.Queue()
    for _ in range(10):
        segmenter._process_frame(_dummy_frame(), out_queue)
        if not out_queue.empty():
            break

    assert out_queue.qsize() == 1
    assert segmenter._is_speaking is False  # после принудительного flush готов к новому сегменту


def test_no_event_before_start_produces_nothing(monkeypatch):
    segmenter = make_segmenter(monkeypatch)
    segmenter._vad_iterator.events = [None, None, None]

    out_queue = queue.Queue()
    for _ in range(3):
        segmenter._process_frame(_dummy_frame(), out_queue)

    assert out_queue.empty()
    assert segmenter._is_speaking is False