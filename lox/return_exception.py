class Return(Exception):
    def __init__(self, value):
        super().__init__()
        self._value = value
