import interpreter
import loxfunction
import loxinstance


class LoxClass:
    def __init__(
        self,
        name: str,
        superclass: LoxClass | None,
        methods: dict[str, loxfunction.LoxFunction],
    ):
        self._name = name
        self._methods = methods
        self._superclass = superclass

    def __str__(self) -> str:
        return self._name

    def call(self, interpret: interpreter.Interpreter, arguments: list[object]):
        instance = loxinstance.LoxInstance(self)
        initializer = self.find_method("init")
        if initializer:
            initializer.bind(instance).call(interpret, arguments)

        return instance

    def arity(self) -> int:
        initializer = self.find_method("init")
        if not initializer:
            return 0
        return initializer.arity()

    def find_method(self, name: str) -> loxfunction.LoxFunction | None:
        if name in self._methods:
            return self._methods[name]

        if self._superclass:
            return self._superclass.find_method(name)

        return None
