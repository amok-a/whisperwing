import logging
import sys

from PyQt6.QtWidgets import QApplication

from . import actions
from .application import Application
from .hotkeys import register_hotkeys
from .llm.factory import get_llm_client
from .logging_config import setup_logging
from .overlay import OverlayWindow
from .signals import Signals

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()

    try:
        llm_client = get_llm_client()
    except Exception as e:
        logger.error(f"Не удалось инициализировать LLM-клиента: {e}")
        return

    qt_app = QApplication(sys.argv)
    signals = Signals()

    app = Application(llm_client, signals)
    app.prepare()

    def on_toggle_listen() -> None:
        actions.toggle_listening(app.listening_event, app.buffer, signals)

    def on_explain() -> None:
        actions.explain_transcript_async(app.buffer, llm_client, signals)

    def on_explain_screen() -> None:
        actions.explain_screen_async(app.buffer, llm_client, signals)

    window = OverlayWindow(signals, on_toggle_listen, on_explain, on_explain_screen)
    window.show()

    app.start()

    qt_app.aboutToQuit.connect(app.stop)

    exit_code = qt_app.exec()
    app.stop()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()