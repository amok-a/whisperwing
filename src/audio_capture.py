import pyaudiowpatch as pyaudio
import threading
import time
import queue


def find_loopback_device(p):
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    if not default_speakers["isLoopbackDevice"]:
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                return loopback
        raise RuntimeError("Не нашли loopback-устройство")
    return default_speakers


def recorder_thread(device, rate, channels, raw_queue: queue.Queue, stop_event: threading.Event):
    """Просто пишет звук и кидает сырые чанки в очередь.
    Нарезкой на фразы теперь занимается VAD-сегментер в отдельном потоке."""
    p = pyaudio.PyAudio()

    def callback(in_data, frame_count, time_info, status):
        raw_queue.put(in_data)
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
