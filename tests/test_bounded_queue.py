from src.bounded_queue import DropOldestQueue


def test_put_within_capacity_keeps_all_items():
    q = DropOldestQueue(maxsize=3, name="test")

    q.put_drop_oldest("a")
    q.put_drop_oldest("b")

    assert q.qsize() == 2
    assert q.get() == "a"
    assert q.get() == "b"


def test_overflow_drops_oldest_item():
    q = DropOldestQueue(maxsize=2, name="test")

    q.put_drop_oldest("first")
    q.put_drop_oldest("second")
    q.put_drop_oldest("third")

    assert q.qsize() == 2
    assert q.get() == "second"
    assert q.get() == "third"


def test_dropped_count_is_tracked():
    q = DropOldestQueue(maxsize=1, name="test")

    q.put_drop_oldest("a")
    assert q.dropped_count == 0

    q.put_drop_oldest("b")
    q.put_drop_oldest("c")

    assert q.dropped_count == 2


def test_queue_never_exceeds_maxsize():
    q = DropOldestQueue(maxsize=5, name="test")

    for i in range(100):
        q.put_drop_oldest(i)

    assert q.qsize() == 5
    remaining = [q.get() for _ in range(5)]
    assert remaining == [95, 96, 97, 98, 99]