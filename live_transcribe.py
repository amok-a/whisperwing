import pyaudiowpatch as pyaudio
import numpy as np
import audioop
from faster_whisper import WhisperModel
import queue
import threading
import time
import traceback
import wave

CHUNK_SECONDS = 8
MODEL_SIZE = "base"
SILENCE_RMS_THRESHOLD = 0.01
SAVE_DEBUG_CHUNKS = True
TARGET_SAMPLE_RATE = 16000

audio_queue = queue.Queue()
stop_event = threading.Event()


def find_loopback_device(p):
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    if not default_speakers["isLoopbackDevice"]:
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                return loopback
        raise RuntimeError("Не нашли loopback-устройство")
    return default_speakers


def save_debug_wav(audio_bytes, rate, channels, filename):
    wf = wave.open(filename, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(2)
    wf.setframerate(rate)
    wf.writeframes(audio_bytes)
    wf.close()


def resample_audio_bytes(audio_bytes, orig_rate, channels, target_rate=TARGET_SAMPLE_RATE):
    if orig_rate == target_rate:
        return audio_bytes
    resampled_bytes, _ = audioop.ratecv(
        audio_bytes, 2, channels, orig_rate, target_rate, None
    )
    return resampled_bytes


def recorder_thread(device, rate, channels):
    p = pyaudio.PyAudio()
    frames = []
    chunk_frame_count = 0
    frames_per_chunk = int(rate * CHUNK_SECONDS)

    def callback(in_data, frame_count, time_info, status):
        nonlocal frames, chunk_frame_count
        frames.append(in_data)
        chunk_frame_count += frame_count
        if chunk_frame_count >= frames_per_chunk:
            audio_queue.put(b"".join(frames))
            frames.clear()
            chunk_frame_count = 0
        return (in_data, pyaudio.paContinue)

    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=rate,
        input=True,
        input_device_index=device["index"],
        stream_callback=callback,
    )
    stream.start_stream()
    print("Слушаю... (Ctrl+C для остановки)")

    while not stop_event.is_set():
        time.sleep(0.2)

    stream.stop_stream()
    stream.close()
    p.terminate()


def transcriber_thread(model, rate, channels):
    chunk_counter = 0

    while not stop_event.is_set():
        try:
            audio_bytes = audio_queue.get(timeout=0.5)
        except queue.Empty:
            continue

        chunk_counter += 1

        try:
            if SAVE_DEBUG_CHUNKS:
                save_debug_wav(audio_bytes, rate, channels, f"debug_chunk_{chunk_counter}.wav")

            # ресемплим ДО конвертации в numpy и ДО сведения в моно
            audio_bytes_16k = resample_audio_bytes(audio_bytes, rate, channels)

            audio_np = np.frombuffer(audio_bytes_16k, dtype=np.int16).astype(np.float32) / 32768.0
            if channels > 1:
                audio_np = audio_np.reshape(-1, channels).mean(axis=1)

            rms = np.sqrt(np.mean(audio_np ** 2))
            if rms < SILENCE_RMS_THRESHOLD:
                print(f"   [{chunk_counter}] (тишина, rms={rms:.4f}, пропускаем)")
                continue

            t0 = time.time()
            segments, info = model.transcribe(
                audio_np,
                language="ru",
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500),
                condition_on_previous_text=False,
            )
            text = " ".join(seg.text for seg in segments).strip()
            elapsed = time.time() - t0

            if text:
                print(f">> [{chunk_counter}] [{elapsed:.1f}s, rms={rms:.3f}] {text}")
            else:
                print(f"   [{chunk_counter}] (пусто после vad, rms={rms:.3f})")
        except Exception:
            print(f"Ошибка в обработке чанка {chunk_counter}:")
            traceback.print_exc()


def main():
    p = pyaudio.PyAudio()
    device = find_loopback_device(p)
    rate = int(device["defaultSampleRate"])
    channels = int(device["maxInputChannels"])
    p.terminate()

    print(f"Устройство: {device['name']}, rate={rate}, channels={channels}")
    print("Загружаю модель Whisper...")
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print("Модель загружена.")

    rec_thread = threading.Thread(target=recorder_thread, args=(device, rate, channels))
    trans_thread = threading.Thread(target=transcriber_thread, args=(model, rate, channels))

    rec_thread.start()
    trans_thread.start()

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