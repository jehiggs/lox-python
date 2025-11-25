import typing

import expr


class AstPrinter:
    def __init__(self):
        pass

    def print(self, expression: typing.Any) -> str:
        return expression.accept(self)

    def visit_binary(self, expression: expr.Binary) -> str:
        return self._parenthesise(
            expression.operator.lexeme, expression.left, expression.right
        )

    def visit_grouping(self, expression: expr.Grouping) -> str:
        return self._parenthesise("group", expression.expression)

    def visit_literal(self, expression: expr.Literal) -> str:
        if expression.value is None:
            return "nil"
        else:
            return str(expression.value)

    def visit_unary(self, expression: expr.Unary) -> str:
        return self._parenthesise(expression.operator.lexeme, expression.right)

    def _parenthesise(self, name: str, *args: typing.Any) -> str:
        expression_string = " ".join([arg.accept(self) for arg in args])
        return f"({name} {expression_string})"


if __name__ == "__main__":
    from tokens import Token, TokenType

    tree = expr.Binary(
        expr.Unary(Token(TokenType.MINUS, "-", None, 1), expr.Literal(123)),
        Token(TokenType.STAR, "*", None, 1),
        expr.Grouping(expr.Literal(45.67)),
    )

    printer = AstPrinter()
    print(printer.print(tree))
