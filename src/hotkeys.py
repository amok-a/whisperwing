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


def register_screen_hotkey(buffer, llm_client):
    def on_hotkey():
        threading.Thread(target=_explain_screen, args=(buffer, llm_client), daemon=True).start()

    keyboard.add_hotkey(config.SCREEN_HOTKEY, on_hotkey)


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


def _explain_screen(buffer, llm_client):
    from .screen_capture import select_region, capture_region

    print("\n[Выдели область экрана мышью, Esc — отмена]\n")
    region = select_region()
    if region is None:
        print("[Отменено]\n")
        return

    x1, y1, x2, y2 = region
    if (x2 - x1) < 10 or (y2 - y1) < 10:
        print("[Область слишком маленькая, отменено]\n")
        return

    image_bytes = capture_region(region)
    context = buffer.get_text()

    print("[Спрашиваю LLM про скриншот...]")
    try:
        answer = llm_client.explain_image(image_bytes, context)
        print(f"\n=== Объяснение скриншота ===\n{answer}\n============================\n")
    except Exception:
        print("Ошибка при запросе к LLM (vision):")
        traceback.print_exc()
