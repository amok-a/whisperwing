import threading

import keyboard

from . import actions, config


def register_hotkeys(buffer, llm_client, listening_event, signals):
    keyboard.add_hotkey(
        config.LISTEN_TOGGLE_HOTKEY,
        lambda: actions.toggle_listening(listening_event, buffer, signals),
    )
    keyboard.add_hotkey(
        config.EXPLAIN_HOTKEY,
        lambda: threading.Thread(
            target=actions.explain_transcript,
            args=(buffer, llm_client, signals),
            daemon=True,
        ).start(),
    )
    keyboard.add_hotkey(
        config.SCREEN_HOTKEY,
        lambda: threading.Thread(
            target=actions.explain_screen,
            args=(buffer, llm_client, signals),
            daemon=True,
        ).start(),
    )
