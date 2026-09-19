import threading

import keyboard

from . import actions, config
from .conversation_buffer import ConversationBuffer
from .llm.base import LLMClient
from .signals import Signals


def register_hotkeys(
    buffer: ConversationBuffer,
    llm_client: LLMClient,
    listening_event: threading.Event,
    signals: Signals,
) -> None:
    keyboard.add_hotkey(
        config.LISTEN_TOGGLE_HOTKEY,
        lambda: actions.toggle_listening(listening_event, buffer, signals),
    )
    keyboard.add_hotkey(
        config.EXPLAIN_HOTKEY,
        lambda: actions.explain_transcript_async(buffer, llm_client, signals),
    )
    keyboard.add_hotkey(
        config.SCREEN_HOTKEY,
        lambda: actions.explain_screen_async(buffer, llm_client, signals),
    )