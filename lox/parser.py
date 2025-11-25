import typing

import errors
import expr
import stmt
import tokens


class Parser:
    def __init__(self, tokens: list[tokens.Token]):
        self._current = 0
        self._tokens = tokens

    def parse(self) -> list[typing.Any]:
        statements = []
        while self._peek().type != tokens.TokenType.EOF:
            statements.append(self._declaration())

        return statements

    def _declaration(self) -> typing.Any:
        try:
            if self._match(tokens.TokenType.CLASS):
                return self._class_declaration()
            elif self._match(tokens.TokenType.FUN):
                return self._function("function")
            elif self._match(tokens.TokenType.VAR):
                return self._var_declaration()

            return self._statement()
        except ParseError:
            self._synchronise()
            return

    def _function(self, kind: str) -> stmt.Function:
        name = self._consume(tokens.TokenType.IDENTIFIER, f"Expect {kind} name.")
        self._consume(
            tokens.TokenType.LEFT_PARENTHESIS, f"Expect '(' after {kind} name."
        )
        params = []
        if not self._check(tokens.TokenType.RIGHT_PARENTHESIS):
            params.append(
                self._consume(tokens.TokenType.IDENTIFIER, "Expect parameter name.")
            )
            while self._match(tokens.TokenType.COMMA):
                if len(params) >= 255:
                    self._error(self._peek(), "Can't have more than 255 parameters.")
                params.append(
                    self._consume(tokens.TokenType.IDENTIFIER, "Expect parameter name.")
                )

        self._consume(
            tokens.TokenType.RIGHT_PARENTHESIS, "Expect ')' after parameters."
        )
        self._consume(tokens.TokenType.LEFT_BRACE, f"Expect '{'{'} before {kind} body.")
        body = self._block()
        return stmt.Function(name, params, body)

    def _class_declaration(self):
        name = self._consume(tokens.TokenType.IDENTIFIER, "Expect class name")

        superclass = None
        if self._match(tokens.TokenType.LESS):
            self._consume(tokens.TokenType.IDENTIFIER, "Expect superclass name.")
            superclass = expr.Variable(self._previous())
        self._consume(tokens.TokenType.LEFT_BRACE, "Expect '{' before class body.")
        methods = []
        while (
            not self._check(tokens.TokenType.RIGHT_BRACE)
            and self._peek().type != tokens.TokenType.EOF
        ):
            methods.append(self._function("method"))

        self._consume(tokens.TokenType.RIGHT_BRACE, "Expect '}' after class body.")
        return stmt.Class(name, superclass, methods)

    def _var_declaration(self) -> typing.Any:
        name = self._consume(tokens.TokenType.IDENTIFIER, "Expect variable name")

        initializer = None
        if self._match(tokens.TokenType.EQUAL):
            initializer = self._expression()

        self._consume(
            tokens.TokenType.SEMICOLON, "Expect ';' after variable declaration"
        )
        return stmt.Var(name, initializer)

    def _statement(self) -> typing.Any:
        if self._match(tokens.TokenType.FOR):
            return self._for_statement()
        elif self._match(tokens.TokenType.IF):
            return self._if_statement()
        elif self._match(tokens.TokenType.PRINT):
            return self._print_statement()
        elif self._match(tokens.TokenType.RETURN):
            return self._return_statement()
        elif self._match(tokens.TokenType.WHILE):
            return self._while_statement()
        elif self._match(tokens.TokenType.LEFT_BRACE):
            return stmt.Block(self._block())

        return self._expression_statement()

    def _for_statement(self):
        self._consume(tokens.TokenType.LEFT_PARENTHESIS, "Expect '(' after for.")
        initializer = None
        if self._match(tokens.TokenType.SEMICOLON):
            initializer = None
        elif self._match(tokens.TokenType.VAR):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()

        condition = None
        if not self._check(tokens.TokenType.SEMICOLON):
            condition = self._expression()

        self._consume(tokens.TokenType.SEMICOLON, "Expect ';' after loop condition.")

        increment = None
        if not self._check(tokens.TokenType.RIGHT_PARENTHESIS):
            increment = self._expression()

        self._consume(
            tokens.TokenType.RIGHT_PARENTHESIS, "Expect ')' after for clause."
        )

        body = self._statement()

        if increment:
            body = stmt.Block([body, stmt.Expression(increment)])

        if not condition:
            condition = expr.Literal(True)

        body = stmt.While(condition, body)

        if initializer:
            body = stmt.Block([initializer, body])

        return body

    def _if_statement(self):
        self._consume(tokens.TokenType.LEFT_PARENTHESIS, "Expect '(' after if.")
        condition = self._expression()
        self._consume(
            tokens.TokenType.RIGHT_PARENTHESIS, "Expect ')' after if condition."
        )

        then_branch = self._statement()
        else_branch = None
        if self._match(tokens.TokenType.ELSE):
            else_branch = self._statement()

        return stmt.If(condition, then_branch, else_branch)

    def _print_statement(self):
        value = self._expression()
        self._consume(tokens.TokenType.SEMICOLON, "Expect ';' after value.")
        return stmt.Print(value)

    def _return_statement(self):
        keyword = self._previous()
        value = None
        if not self._check(tokens.TokenType.SEMICOLON):
            value = self._expression()

        self._consume(tokens.TokenType.SEMICOLON, "Expect ';' after return value.")
        return stmt.Return(keyword, value)

    def _while_statement(self):
        self._consume(tokens.TokenType.LEFT_PARENTHESIS, "Expect '(' after 'while'.")
        condition = self._expression()
        self._consume(
            tokens.TokenType.RIGHT_PARENTHESIS, "Expect ')' after while condition."
        )
        body = self._statement()

        return stmt.While(condition, body)

    def _block(self) -> list[object]:
        statements = []
        while (
            not self._check(tokens.TokenType.RIGHT_BRACE)
            and self._peek().type != tokens.TokenType.EOF
        ):
            statements.append(self._declaration())

        self._consume(tokens.TokenType.RIGHT_BRACE, "Expect '}' after block")
        return statements

    def _expression_statement(self):
        expression = self._expression()
        self._consume(tokens.TokenType.SEMICOLON, "Expect ';' after expression")
        return stmt.Expression(expression)

    def _expression(self) -> typing.Any:
        return self._assignment()

    def _assignment(self) -> typing.Any:
        expression = self._or()

        if self._match(tokens.TokenType.EQUAL):
            equals = self._previous()
            value = self._assignment()

            if isinstance(expression, expr.Variable):
                return expr.Assign(expression.name, value)
            elif isinstance(expression, expr.Get):
                return expr.Set(expression.instance, expression.name, value)

            self._error(equals, "Invalid assignment target.")

        return expression

    def _or(self):
        expression = self._and()
        while self._match(tokens.TokenType.OR):
            operator = self._previous()
            right = self._and()
            expression = expr.Logical(expression, operator, right)

        return expression

    def _and(self):
        expression = self._equality()
        while self._match(tokens.TokenType.AND):
            operator = self._previous()
            right = self._equality()
            expression = expr.Logical(expression, operator, right)

        return expression

    def _equality(self):
        expression = self._comparison()

        while self._match(tokens.TokenType.BANG_EQUAL, tokens.TokenType.EQUAL_EQUAL):
            operator = self._previous()
            right = self._comparison()
            expression = expr.Binary(expression, operator, right)

        return expression

    def _comparison(self) -> typing.Any:
        expression = self._term()
        while self._match(
            tokens.TokenType.GREATER,
            tokens.TokenType.GREATER_EQUAL,
            tokens.TokenType.LESS,
            tokens.TokenType.LESS_EQUAL,
        ):
            operator = self._previous()
            right = self._term()
            expression = expr.Binary(expression, operator, right)

        return expression

    def _term(self) -> typing.Any:
        expression = self._factor()
        while self._match(tokens.TokenType.PLUS, tokens.TokenType.MINUS):
            operator = self._previous()
            right = self._factor()
            expression = expr.Binary(expression, operator, right)

        return expression

    def _factor(self) -> typing.Any:
        expression = self._unary()
        while self._match(tokens.TokenType.SLASH, tokens.TokenType.STAR):
            operator = self._previous()
            right = self._unary()
            expression = expr.Binary(expression, operator, right)

        return expression

    def _unary(self) -> typing.Any:
        if self._match(tokens.TokenType.BANG, tokens.TokenType.MINUS):
            operator = self._previous()
            right = self._unary()
            return expr.Unary(operator, right)

        return self._call()

    def _call(self) -> typing.Any:
        expression = self._primary()
        while True:
            if self._match(tokens.TokenType.LEFT_PARENTHESIS):
                expression = self._finish_call(expression)
            elif self._match(tokens.TokenType.DOT):
                name = self._consume(
                    tokens.TokenType.IDENTIFIER, "Expect property name after '.'."
                )
                expression = expr.Get(expression, name)
            else:
                break

        return expression

    def _finish_call(self, expression: typing.Any):
        arguments = []
        if not self._check(tokens.TokenType.RIGHT_PARENTHESIS):
            arguments.append(self._expression())
            while self._match(tokens.TokenType.COMMA):
                if len(arguments) >= 255:
                    self._error(self._peek(), "Can't have more than 255 arguments.")
                arguments.append(self._expression())

        paren = self._consume(
            tokens.TokenType.RIGHT_PARENTHESIS, "Expect ')' after arguments."
        )
        return expr.Call(expression, paren, arguments)

    def _primary(self) -> typing.Any:
        if self._match(tokens.TokenType.FALSE):
            return expr.Literal(False)
        elif self._match(tokens.TokenType.TRUE):
            return expr.Literal(True)
        elif self._match(tokens.TokenType.NIL):
            return expr.Literal(None)
        elif self._match(tokens.TokenType.NUMBER, tokens.TokenType.STRING):
            return expr.Literal(self._previous().literal)
        elif self._match(tokens.TokenType.SUPER):
            keyword = self._previous()
            self._consume(tokens.TokenType.DOT, "Expect '.' after 'super.")
            method = self._consume(
                tokens.TokenType.IDENTIFIER, "Expect superclass method name."
            )
            return expr.Super(keyword, method)
        elif self._match(tokens.TokenType.THIS):
            return expr.This(self._previous())
        elif self._match(tokens.TokenType.IDENTIFIER):
            return expr.Variable(self._previous())
        elif self._match(tokens.TokenType.LEFT_PARENTHESIS):
            expression = self._expression()
            self._consume(
                tokens.TokenType.RIGHT_PARENTHESIS, "Expect ')' after expression"
            )
            return expr.Grouping(expression)
        else:
            raise self._error(self._peek(), "Expect expression.")

    def _match(self, *args) -> bool:
        matches = any(self._check(type) for type in args)
        if matches:
            self._advance()

        return matches

    def _check(self, type: tokens.TokenType) -> bool:
        token = self._peek()
        return token.type == type and token.type is not tokens.TokenType.EOF

    def _advance(self) -> tokens.Token:
        if self._peek().type is not tokens.TokenType.EOF:
            self._current += 1
        return self._previous()

    def _previous(self) -> tokens.Token:
        return self._tokens[self._current - 1]

    def _peek(self) -> tokens.Token:
        return self._tokens[self._current]

    def _consume(self, type: tokens.TokenType, message: str):
        if self._check(type):
            return self._advance()

        raise self._error(self._peek(), message)

    def _error(self, token: tokens.Token, message: str) -> ParseError:
        if token.type == tokens.TokenType.EOF:
            errors.report(token.line, " at end", message)
        else:
            errors.report(token.line, f" at '{token.lexeme}'", message)

        return ParseError()

    def _synchronise(self):
        self._advance()

        while self._peek().type is not tokens.TokenType.EOF:
            if self._previous().type == tokens.TokenType.SEMICOLON:
                return

            if self._peek().type in {
                tokens.TokenType.CLASS,
                tokens.TokenType.FUN,
                tokens.TokenType.VAR,
                tokens.TokenType.FOR,
                tokens.TokenType.IF,
                tokens.TokenType.WHILE,
                tokens.TokenType.RETURN,
            }:
                return

            self._advance()


class ParseError(Exception):
    pass
