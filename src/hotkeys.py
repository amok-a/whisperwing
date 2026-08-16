import threading
import traceback
import keyboard

from . import config


def register_explain_hotkey(buffer, llm_client):
    def on_hotkey():
        threading.Thread(target=_explain, args=(buffer, llm_client), daemon=True).start()

    keyboard.add_hotkey(config.EXPLAIN_HOTKEY, on_hotkey)


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
