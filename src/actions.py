import logging

from .screen_capture import capture_region, select_region

logger = logging.getLogger(__name__)


def toggle_listening(listening_event, buffer, signals):
    if listening_event.is_set():
        listening_event.clear()
        msg = "Прослушивание остановлено"
    else:
        buffer.clear()
        listening_event.set()
        msg = "Прослушивание запущено (буфер очищен)"
    logger.info(msg)
    signals.status_changed.emit(msg)


def explain_transcript(buffer, llm_client, signals):
    transcript = buffer.get_text()
    if not transcript:
        signals.explanation_ready.emit("Буфер пуст — пока нечего объяснять.")
        return

    signals.status_changed.emit("Спрашиваю LLM...")
    try:
        answer = llm_client.explain(transcript)
        logger.info(f"Объяснение получено ({len(answer)} символов)")
        signals.explanation_ready.emit(answer)
    except Exception:
        logger.exception("Ошибка при запросе к LLM")
        signals.explanation_ready.emit("Ошибка при запросе к LLM (см. логи).")


def explain_screen(buffer, llm_client, signals):
    try:
        logger.debug("Открываю окно выделения области")
        signals.status_changed.emit("Выдели область экрана мышью, Esc — отмена")
        region = select_region()
        logger.debug(f"Выделено: {region}")

        if region is None:
            signals.status_changed.emit("Захват экрана отменён")
            return

        x1, y1, x2, y2 = region
        if (x2 - x1) < 10 or (y2 - y1) < 10:
            logger.debug("Область слишком маленькая, отмена")
            signals.status_changed.emit("Область слишком маленькая")
            return

        logger.debug("Делаю скриншот...")
        image_bytes = capture_region(region)
        logger.debug(f"Скриншот готов, {len(image_bytes)} байт")

        context = buffer.get_text()

        logger.debug("Отправляю в LLM...")
        signals.status_changed.emit("Спрашиваю LLM про скриншот...")
        answer = llm_client.explain_image(image_bytes, context)
        logger.info("Ответ по скриншоту получен")
        signals.screen_explanation_ready.emit(answer)
    except Exception:
        logger.exception("Ошибка при обработке скриншота")
        signals.screen_explanation_ready.emit("Ошибка при запросе к LLM (см. логи).")
