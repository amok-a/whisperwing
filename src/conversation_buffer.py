import threading
import time
from collections import deque

from . import config


class ConversationBuffer:
    def __init__(self, minutes: int = config.BUFFER_MINUTES) -> None:
        self._minutes = minutes
        self._items: deque[tuple[float, str]] = deque()
        self._lock = threading.Lock()

    def append(self, text: str) -> None:
        now = time.time()
        with self._lock:
            self._items.append((now, text))
            cutoff = now - self._minutes * 60
            while self._items and self._items[0][0] < cutoff:
                self._items.popleft()

    def get_text(self) -> str:
        with self._lock:
            return " ".join(text for _, text in self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()