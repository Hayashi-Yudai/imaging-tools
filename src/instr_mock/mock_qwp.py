class MockQWP:
    def __init__(self, init_position=False):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return None

    def wait_while_busy(self):
        return None

    def move(self, angle: int, axis: int = 1):
        return None
