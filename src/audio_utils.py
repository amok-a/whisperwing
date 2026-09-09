import audioop


def resample_audio_bytes(audio_bytes: bytes, orig_rate: int, channels: int, target_rate: int) -> bytes:
    """Ресемплит PCM16-байты до target_rate, сводя многоканальный звук в моно."""
    if channels > 1:
        audio_bytes = audioop.tomono(audio_bytes, 2, 0.5, 0.5)
    if orig_rate == target_rate:
        return audio_bytes
    resampled, _ = audioop.ratecv(audio_bytes, 2, 1, orig_rate, target_rate, None)
    return resampled
