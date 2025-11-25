import tokens


class LoxError(Exception):
    def __init__(self, line: int, where: str, message: str):
        self._line = line
        self._where = where
        self._message = message

    def __str__(self) -> str:
        return f"[Line {self._line}] Error {self._where}: {self._message}"


class RuntimeError(Exception):
    def __init__(self, token: tokens.Token, message: str):
        super().__init__(message)
        self.token = token


_has_error = False
_has_runtime_error = False


def report(line: int, where: str, message: str):
    global _has_error
    _has_error = True
    print(f"[Line {line}] Error {where}: {message}")


def is_error() -> bool:
    return _has_error


def is_runtime_error() -> bool:
    return _has_runtime_error


def reset():
    _has_error = False


def runtime_error(error: RuntimeError):
    print(f"{error}: \n[line {error.token.line}]")
    _has_runtime_error = True
