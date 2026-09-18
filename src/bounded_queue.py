import logging
import queue
from typing import Any

logger = logging.getLogger(__name__)


class DropOldestQueue(queue.Queue):
    """Очередь с ограниченным размером, которая при переполнении выбрасывает
    самый старый элемент вместо блокировки."""

    def __init__(self, maxsize: int, name: str = "queue") -> None:
        super().__init__(maxsize=maxsize)
        self._name = name
        self._dropped_count = 0

    def put_drop_oldest(self, item: Any) -> None:
        while True:
            try:
                self.put_nowait(item)
                return
            except queue.Full:
                try:
                    self.get_nowait()
                    self._dropped_count += 1
                    if self._dropped_count % 50 == 1:
                        logger.warning(
                            f"{self._name}: обработка не успевает за входным потоком, "
                            f"отброшено элементов: {self._dropped_count}"
                        )
                except queue.Empty:
                    continue

    @property
    def dropped_count(self) -> int:
        return self._dropped_count