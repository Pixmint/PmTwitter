from utils.topics import get_thread_id


class Dummy:
    def __init__(self, thread_id):
        self.message_thread_id = thread_id


def test_get_thread_id():
    msg = Dummy(123)
    assert get_thread_id(msg) == 123
