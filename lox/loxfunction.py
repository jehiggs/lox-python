import environment
import interpreter
import loxinstance
import return_exception
import stmt


class LoxFunction:
    def __init__(
        self,
        declaration: stmt.Function,
        closure: environment.Environment,
        is_initializer: bool,
    ):
        self._declaration = declaration
        self._closure = closure
        self._is_initializer = is_initializer

    def call(self, interpret: interpreter.Interpreter, arguments: list[object]):
        env = environment.Environment(self._closure)
        for dec, arg in zip(self._declaration.params, arguments):
            env.define(dec.lexeme, arg)

        try:
            interpret._execute_block(self._declaration.body, env)
        except return_exception.Return as e:
            if self._is_initializer:
                return self._closure.get_at(0, "this")
            return e._value

        if self._is_initializer:
            return self._closure.get_at(0, "this")
        return None

    def arity(self) -> int:
        return len(self._declaration.params)

    def bind(self, instance: loxinstance.LoxInstance) -> LoxFunction:
        env = environment.Environment(self._closure)
        env.define("this", instance)
        return LoxFunction(self._declaration, env, self._is_initializer)

    def __str__(self) -> str:
        return f"<fn {self._declaration.name.lexeme}>"
