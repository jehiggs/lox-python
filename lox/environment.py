import typing

import errors
import tokens


class Environment:
    def __init__(self, enclosing: Environment | None = None):
        self.values: dict[str, typing.Any] = {}
        self._enclosing: Environment | None = enclosing

    def define(self, name: str, value: typing.Any):
        self.values[name] = value

    def get(self, name: tokens.Token) -> typing.Any:
        if name.lexeme in self.values:
            return self.values[name.lexeme]

        if self._enclosing:
            return self._enclosing.get(name)

        raise errors.RuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def assign(self, name: tokens.Token, value: typing.Any):
        if name.lexeme in self.values:
            self.values[name.lexeme] = value
            return

        if self._enclosing:
            return self._enclosing.assign(name, value)

        raise errors.RuntimeError(name, f"Undefined variable '{name.lexeme}'.")

    def get_at(self, distance: int, name: str) -> object:
        return self._ancestor(distance).values.get(name)

    def _ancestor(self, distance: int) -> Environment:
        env = self
        for _ in range(distance):
            env = env._enclosing

        return env

    def assign_at(self, distance: int, name: tokens.Token, value: object):
        env = self._ancestor(distance)
        env.values[name.lexeme] = value
