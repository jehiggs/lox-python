import errors
import loxclass
import tokens


class LoxInstance:
    def __init__(self, klass: loxclass.LoxClass):
        self._klass = klass
        self._fields: dict[str, object] = {}

    def __str__(self) -> str:
        return f"{self._klass} instance"

    def get(self, name: tokens.Token):
        if name.lexeme in self._fields:
            return self._fields[name.lexeme]

        method = self._klass.find_method(name.lexeme)
        if method:
            return method.bind(self)

        raise errors.RuntimeError(name, f"Undefined property '{name.lexeme}'")

    def set(self, name: tokens.Token, value: object):
        self._fields[name.lexeme] = value
