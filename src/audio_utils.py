import numpy as np
import soxr


def resample_audio_bytes(
    audio_bytes: bytes, orig_rate: int, channels: int, target_rate: int
) -> bytes:
    """Ресемплит PCM16-байты до target_rate, сводя многоканальный звук в моно.
    Разовый (stateless) вызов — для потоковой обработки с сохранением
    состояния между чанками (без щелчков на границах) см.
    VadSegmenter._to_16k_mono в vad_segmenter.py."""
    audio_np = np.frombuffer(audio_bytes, dtype=np.int16)
    if channels > 1:
        audio_np = audio_np.reshape(-1, channels).mean(axis=1)

    if orig_rate == target_rate:
        return audio_np.astype(np.int16).tobytes()

    audio_float = audio_np.astype(np.float32) / 32768.0
    resampled = soxr.resample(audio_float, orig_rate, target_rate)
    resampled_int16 = np.clip(resampled * 32768.0, -32768, 32767).astype(np.int16)
    return resampled_int16.tobytes()
