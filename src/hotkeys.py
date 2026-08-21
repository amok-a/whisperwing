import threading
import traceback
import keyboard

from . import config


def register_explain_hotkey(buffer, llm_client):
    def on_hotkey():
        threading.Thread(target=_explain, args=(buffer, llm_client), daemon=True).start()

    keyboard.add_hotkey(config.EXPLAIN_HOTKEY, on_hotkey)


def register_listen_toggle_hotkey(listening_event: threading.Event, buffer):
    def on_toggle():
        if listening_event.is_set():
            listening_event.clear()
            print("\n[⏸ Прослушивание остановлено]\n")
        else:
            buffer.clear()
            listening_event.set()
            print("\n[▶ Прослушивание запущено (буфер очищен)]\n")

    keyboard.add_hotkey(config.LISTEN_TOGGLE_HOTKEY, on_toggle)


def _explain(buffer, llm_client):
    transcript = buffer.get_text()
    if not transcript:
        print("\n[Буфер пуст — пока нечего объяснять]\n")
        return

    print("\n[Спрашиваю LLM...]")
    try:
        answer = llm_client.explain(transcript)
        print(f"\n=== Объяснение ===\n{answer}\n===================\n")
    except Exception:
        print("Ошибка при запросе к LLM:")
        traceback.print_exc()