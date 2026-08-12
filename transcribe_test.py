from faster_whisper import WhisperModel

MODEL_SIZE = "small"
AUDIO_FILE = "test_output.wav"

def main():
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")

    segments, info = model.transcribe(AUDIO_FILE, language="ru")

    print(f"Detected language: {info.language} (probability {info.language_probability:.2f})")
    print("---")

    for segment in segments:
        print(f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}")

if __name__ == "__main__":
    main()
