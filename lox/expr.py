import dataclasses
import typing

import tokens


@dataclasses.dataclass(frozen=True)
class Assign:
    name: tokens.Token
    value: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_assign(self)


@dataclasses.dataclass(frozen=True)
class Binary:
    left: object
    operator: tokens.Token
    right: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_binary(self)


@dataclasses.dataclass(frozen=True)
class Call:
    callee: object
    paren: tokens.Token
    arguments: list[object]

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_call(self)


@dataclasses.dataclass(frozen=True)
class Get:
    instance: object
    name: tokens.Token

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_get(self)


@dataclasses.dataclass(frozen=True)
class Grouping:
    expression: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_grouping(self)


@dataclasses.dataclass(frozen=True)
class Literal:
    value: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_literal(self)


@dataclasses.dataclass(frozen=True)
class Logical:
    left: object
    operator: tokens.Token
    right: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_logical(self)


@dataclasses.dataclass(frozen=True)
class Set:
    instance: object
    name: tokens.Token
    value: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_set(self)


@dataclasses.dataclass(frozen=True)
class Super:
    keyword: tokens.Token
    method: tokens.Token

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_super(self)


@dataclasses.dataclass(frozen=True)
class This:
    keyword: tokens.Token

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_this(self)


@dataclasses.dataclass(frozen=True)
class Unary:
    operator: tokens.Token
    right: object

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_unary(self)


@dataclasses.dataclass(frozen=True)
class Variable:
    name: tokens.Token

    def accept(self, visitor: typing.Any) -> object | None:
        return visitor.visit_variable(self)
