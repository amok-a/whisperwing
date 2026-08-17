import webrtcvad
import audioop
import queue
import threading
import time

from . import config

FRAME_MS = 30
BYTES_PER_SAMPLE = 2  # 16-bit PCM
FRAME_BYTES_16K_MONO = int(config.TARGET_SAMPLE_RATE * FRAME_MS / 1000) * BYTES_PER_SAMPLE


class VadSegmenter:

    def __init__(self, orig_rate: int, channels: int):
        self._orig_rate = orig_rate
        self._channels = channels
        self._vad = webrtcvad.Vad(config.VAD_AGGRESSIVENESS)

        self._resample_state = None
        self._pending_bytes = b""
        self._segment_buffer = bytearray()
        self._is_speaking = False
        self._silence_start = None

    def process_raw_chunk(self, raw_bytes: bytes, out_queue: queue.Queue):
        mono_16k = self._to_16k_mono(raw_bytes)
        self._pending_bytes += mono_16k

        while len(self._pending_bytes) >= FRAME_BYTES_16K_MONO:
            frame = self._pending_bytes[:FRAME_BYTES_16K_MONO]
            self._pending_bytes = self._pending_bytes[FRAME_BYTES_16K_MONO:]
            self._process_frame(frame, out_queue)

    def _to_16k_mono(self, raw_bytes: bytes) -> bytes:
        if self._channels > 1:
            raw_bytes = audioop.tomono(raw_bytes, 2, 0.5, 0.5)
        resampled, self._resample_state = audioop.ratecv(
            raw_bytes, 2, 1, self._orig_rate, config.TARGET_SAMPLE_RATE, self._resample_state
        )
        return resampled

    def _process_frame(self, frame: bytes, out_queue: queue.Queue):
        is_speech = self._vad.is_speech(frame, config.TARGET_SAMPLE_RATE)
        now = time.time()

        if is_speech:
            if not self._is_speaking:
                self._is_speaking = True
                self._segment_buffer = bytearray()
            self._segment_buffer.extend(frame)
            self._silence_start = None

            duration = len(self._segment_buffer) / BYTES_PER_SAMPLE / config.TARGET_SAMPLE_RATE
            if duration >= config.VAD_MAX_SEGMENT_SECONDS:
                self._flush(out_queue)
        else:
            if self._is_speaking:
                self._segment_buffer.extend(frame)
                if self._silence_start is None:
                    self._silence_start = now
                elif now - self._silence_start >= config.VAD_SILENCE_MS / 1000:
                    self._flush(out_queue)

    def _flush(self, out_queue: queue.Queue):
        duration = len(self._segment_buffer) / BYTES_PER_SAMPLE / config.TARGET_SAMPLE_RATE
        if duration >= config.VAD_MIN_SEGMENT_SECONDS:
            out_queue.put(bytes(self._segment_buffer))
        self._segment_buffer = bytearray()
        self._is_speaking = False
        self._silence_start = None


def segmenter_thread(orig_rate, channels, raw_queue: queue.Queue, speech_queue: queue.Queue, stop_event: threading.Event):
    segmenter = VadSegmenter(orig_rate, channels)

    while not stop_event.is_set():
        try:
            raw_bytes = raw_queue.get(timeout=0.5)
        except queue.Empty:
            continue
        segmenter.process_raw_chunk(raw_bytes, speech_queue)
