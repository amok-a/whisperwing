import math
import struct

from src.audio_utils import resample_audio_bytes


def _sine_wave_pcm16(duration_seconds: float, sample_rate: int, channels: int = 1) -> bytes:
    """Генерирует синусоиду в формате PCM16 для тестового аудио —
    не важен сам звук, важна только правильная длина/формат данных."""
    num_samples = int(duration_seconds * sample_rate)
    samples = []
    for i in range(num_samples):
        value = int(3000 * math.sin(2 * math.pi * 440 * i / sample_rate))
        for _ in range(channels):
            samples.append(value)
    return struct.pack(f"<{len(samples)}h", *samples)


def test_same_rate_returns_bytes_unchanged():
    audio = _sine_wave_pcm16(0.5, 16000)
    result = resample_audio_bytes(audio, orig_rate=16000, channels=1, target_rate=16000)
    assert result == audio


def test_downsample_mono_produces_expected_length():
    audio = _sine_wave_pcm16(1.0, 48000, channels=1)
    result = resample_audio_bytes(audio, orig_rate=48000, channels=1, target_rate=16000)

    expected_samples = 16000  # 1 секунда на целевой частоте
    actual_samples = len(result) // 2  # 2 байта на сэмпл (PCM16)

    assert abs(actual_samples - expected_samples) < 50


def test_downsample_stereo_produces_expected_length():
    audio = _sine_wave_pcm16(1.0, 48000, channels=2)
    result = resample_audio_bytes(audio, orig_rate=48000, channels=2, target_rate=16000)

    expected_samples = 16000 * 2  # 2 канала
    actual_samples = len(result) // 2

    assert abs(actual_samples - expected_samples) < 100
