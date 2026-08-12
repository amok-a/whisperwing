import pyaudiowpatch as pyaudio
import audioop
import threading
import time
import wave
import queue

from . import config


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


def resample_audio_bytes(audio_bytes, orig_rate, channels, target_rate=config.TARGET_SAMPLE_RATE):
    if orig_rate == target_rate:
        return audio_bytes
    resampled_bytes, _ = audioop.ratecv(audio_bytes, 2, channels, orig_rate, target_rate, None)
    return resampled_bytes


def recorder_thread(device, rate, channels, audio_queue: queue.Queue, stop_event: threading.Event):
    p = pyaudio.PyAudio()
    frames = []
    chunk_frame_count = 0
    frames_per_chunk = int(rate * config.CHUNK_SECONDS)

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

    while not stop_event.is_set():
        time.sleep(0.2)

    stream.stop_stream()
    stream.close()
    p.terminate()
