import audioop
import queue
import threading

import numpy as np
import torch
from silero_vad import VADIterator, load_silero_vad

from . import config

WINDOW_SAMPLES = 512
BYTES_PER_SAMPLE = 2
WINDOW_BYTES = WINDOW_SAMPLES * BYTES_PER_SAMPLE


class VadSegmenter:
    def __init__(self, orig_rate: int, channels: int) -> None:
        self._orig_rate = orig_rate
        self._channels = channels

        self._model = load_silero_vad()
        self._vad_iterator = VADIterator(
            self._model,
            sampling_rate=config.TARGET_SAMPLE_RATE,
            threshold=config.VAD_THRESHOLD,
            min_silence_duration_ms=config.VAD_SILENCE_MS,
            speech_pad_ms=config.VAD_SPEECH_PAD_MS,
        )

        self._resample_state = None
        self._pending_bytes = b""
        self._segment_buffer = bytearray()
        self._is_speaking = False

    def process_raw_chunk(self, raw_bytes: bytes, out_queue: queue.Queue) -> None:
        mono_16k = self._to_16k_mono(raw_bytes)
        self._pending_bytes += mono_16k

        while len(self._pending_bytes) >= WINDOW_BYTES:
            frame_bytes = self._pending_bytes[:WINDOW_BYTES]
            self._pending_bytes = self._pending_bytes[WINDOW_BYTES:]
            self._process_frame(frame_bytes, out_queue)

    def _to_16k_mono(self, raw_bytes: bytes) -> bytes:
        if self._channels > 1:
            raw_bytes = audioop.tomono(raw_bytes, 2, 0.5, 0.5)
        resampled, self._resample_state = audioop.ratecv(
            raw_bytes, 2, 1, self._orig_rate, config.TARGET_SAMPLE_RATE, self._resample_state
        )
        return resampled

    def _process_frame(self, frame_bytes: bytes, out_queue: queue.Queue) -> None:
        if self._is_speaking:
            self._segment_buffer.extend(frame_bytes)

        audio_np = np.frombuffer(frame_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        audio_tensor = torch.from_numpy(audio_np)
        event = self._vad_iterator(audio_tensor, return_seconds=False)

        if event is not None:
            if "start" in event and not self._is_speaking:
                self._is_speaking = True
                self._segment_buffer = bytearray(frame_bytes)
            elif "end" in event and self._is_speaking:
                self._flush(out_queue)
                return

        if self._is_speaking:
            duration = len(self._segment_buffer) / BYTES_PER_SAMPLE / config.TARGET_SAMPLE_RATE
            if duration >= config.VAD_MAX_SEGMENT_SECONDS:
                self._flush(out_queue)

    def _flush(self, out_queue: queue.Queue) -> None:
        duration = len(self._segment_buffer) / BYTES_PER_SAMPLE / config.TARGET_SAMPLE_RATE
        if duration >= config.VAD_MIN_SEGMENT_SECONDS:
            out_queue.put(bytes(self._segment_buffer))
        self._segment_buffer = bytearray()
        self._is_speaking = False


def segmenter_thread(
    orig_rate: int,
    channels: int,
    raw_queue: queue.Queue,
    speech_queue: queue.Queue,
    stop_event: threading.Event,
) -> None:
    segmenter = VadSegmenter(orig_rate, channels)

    while not stop_event.is_set():
        try:
            raw_bytes = raw_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        segmenter.process_raw_chunk(raw_bytes, speech_queue)
