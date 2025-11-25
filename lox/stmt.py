import dataclasses
import typing

import tokens


@dataclasses.dataclass(frozen=True)
class Block:
    statements: list[object]

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_block(self)


@dataclasses.dataclass(frozen=True)
class Class:
    name: tokens.Token
    superclass: typing.Any
    methods: list[Function]

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_class(self)


@dataclasses.dataclass(frozen=True)
class Expression:
    expression: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_expression(self)


@dataclasses.dataclass(frozen=True)
class Function:
    name: tokens.Token
    params: list[tokens.Token]
    body: list[object]

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_function(self)


@dataclasses.dataclass(frozen=True)
class If:
    condition: object
    then_branch: object
    else_branch: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_if(self)


@dataclasses.dataclass(frozen=True)
class Print:
    expression: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_print(self)


@dataclasses.dataclass(frozen=True)
class Return:
    keyword: tokens.Token
    value: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_return(self)


@dataclasses.dataclass(frozen=True)
class Var:
    name: tokens.Token
    initializer: typing.Any

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_var(self)


@dataclasses.dataclass(frozen=True)
class While:
    condition: typing.Any
    body: typing.Any

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_while(self)
