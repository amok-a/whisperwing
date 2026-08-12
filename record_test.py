import pyaudiowpatch as pyaudio
import wave

DURATION = 10  # секунд
OUTPUT_FILE = "test_output.wav"

def main():
    p = pyaudio.PyAudio()

    # находим WASAPI info и default speakers (loopback-устройство)
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

    if not default_speakers["isLoopbackDevice"]:
        # ищем loopback-версию этого устройства среди всех устройств
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                default_speakers = loopback
                break
        else:
            raise RuntimeError("Не нашли loopback-устройство. Пришли список устройств — разберёмся.")

    print(f"Записываем с устройства: {default_speakers['name']}")

    channels = int(default_speakers["maxInputChannels"])
    rate = int(default_speakers["defaultSampleRate"])

    frames = []

    def callback(in_data, frame_count, time_info, status):
        frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    stream = p.open(
        format=pyaudio.paInt16,
        channels=channels,
        rate=rate,
        input=True,
        input_device_index=default_speakers["index"],
        stream_callback=callback,
    )

    print(f"Говори что-нибудь в динамики (или включи музыку) на {DURATION} секунд...")
    stream.start_stream()
    import time
    time.sleep(DURATION)
    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(OUTPUT_FILE, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
    wf.setframerate(rate)
    wf.writeframes(b"".join(frames))
    wf.close()

    print(f"Готово! Записано в {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
