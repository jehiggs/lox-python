import time


class Clock:
    def __init__(self):
        pass

    def arity(self) -> int:
        return 0

    def call(self, interpreter, args):
        nanos = time.time_ns()
        return nanos / 1000000

    def __str__(self):
        return "<native function> time"
