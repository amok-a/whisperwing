from src.conversation_buffer import ConversationBuffer
import src.conversation_buffer as buffer_module


def _freeze_time(monkeypatch, start=1000.0):
    """Подменяет time.time() внутри conversation_buffer на управляемое
    тестом значение, чтобы проверять обрезку буфера по времени детерминированно."""
    current = {"t": start}
    monkeypatch.setattr(buffer_module.time, "time", lambda: current["t"])
    return current


def test_append_and_get_text(monkeypatch):
    _freeze_time(monkeypatch)
    buf = ConversationBuffer(minutes=5)

    buf.append("привет")
    buf.append("как дела")

    assert buf.get_text() == "привет как дела"


def test_empty_buffer_returns_empty_string():
    buf = ConversationBuffer(minutes=5)
    assert buf.get_text() == ""


def test_old_items_are_pruned_outside_window(monkeypatch):
    clock = _freeze_time(monkeypatch, start=0.0)
    buf = ConversationBuffer(minutes=5)  # окно 300 секунд

    buf.append("старое сообщение")

    clock["t"] = 301.0  # шагнули за пределы окна
    buf.append("новое сообщение")

    assert buf.get_text() == "новое сообщение"


def test_items_within_window_are_kept(monkeypatch):
    clock = _freeze_time(monkeypatch, start=0.0)
    buf = ConversationBuffer(minutes=5)

    buf.append("первое")

    clock["t"] = 299.0  # ещё внутри окна (< 300 секунд)
    buf.append("второе")

    assert buf.get_text() == "первое второе"


def test_clear_empties_buffer(monkeypatch):
    _freeze_time(monkeypatch)
    buf = ConversationBuffer(minutes=5)

    buf.append("что-то")
    buf.clear()

    assert buf.get_text() == ""