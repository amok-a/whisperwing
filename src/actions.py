import traceback

from .screen_capture import select_region, capture_region


def toggle_listening(listening_event, buffer, signals):
    if listening_event.is_set():
        listening_event.clear()
        msg = "⏸ Прослушивание остановлено"
    else:
        buffer.clear()
        listening_event.set()
        msg = "▶ Прослушивание запущено (буфер очищен)"
    print(f"\n[{msg}]\n")
    signals.status_changed.emit(msg)


def explain_transcript(buffer, llm_client, signals):
    transcript = buffer.get_text()
    if not transcript:
        signals.explanation_ready.emit("Буфер пуст — пока нечего объяснять.")
        return

    signals.status_changed.emit("Спрашиваю LLM...")
    try:
        answer = llm_client.explain(transcript)
        signals.explanation_ready.emit(answer)
    except Exception:
        traceback.print_exc()
        signals.explanation_ready.emit("Ошибка при запросе к LLM (см. консоль).")


def explain_screen(buffer, llm_client, signals):
    signals.status_changed.emit("Выдели область экрана мышью, Esc — отмена")
    region = select_region()
    if region is None:
        signals.status_changed.emit("Захват экрана отменён")
        return

    x1, y1, x2, y2 = region
    if (x2 - x1) < 10 or (y2 - y1) < 10:
        signals.status_changed.emit("Область слишком маленькая")
        return

    image_bytes = capture_region(region)
    context = buffer.get_text()

    signals.status_changed.emit("Спрашиваю LLM про скриншот...")
    try:
        answer = llm_client.explain_image(image_bytes, context)
        signals.screen_explanation_ready.emit(answer)
    except Exception:
        traceback.print_exc()
        signals.screen_explanation_ready.emit("Ошибка при запросе к LLM (см. консоль).")
