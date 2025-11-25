import enum
import typing

import errors
import expr
import interpreter
import stmt
import tokens


class Resolver:
    def __init__(self, interpret: interpreter.Interpreter):
        self._interpreter = interpret
        self._scopes: list[dict[str, bool]] = []
        self._current_function = FunctionType.NONE
        self._current_class = ClassType.NONE

    def visit_block(self, block: stmt.Block):
        self._begin_scope()
        self._resolve(block.statements)
        self._end_scope()
        return None

    def visit_var(self, var: stmt.Var):
        self._declare(var.name)
        if var.initializer is not None:
            self._resolve(var.initializer)

        self._define(var.name)
        return None

    def visit_variable(self, variable: expr.Variable):
        if (
            len(self._scopes) != 0
            and self._scopes[-1].get(variable.name.lexeme) == False
        ):
            self._error(
                variable.name, "Can't read local variable in its own initializer."
            )

        self._resolve_local(variable, variable.name)

    def visit_assign(self, assignment: expr.Assign):
        self._resolve(assignment.value)
        self._resolve_local(assignment, assignment.name)

    def visit_function(self, function: stmt.Function):
        self._declare(function.name)
        self._define(function.name)

        self._resolve_function(function, FunctionType.FUNCTION)

    def visit_expression(self, expression: stmt.Expression):
        self._resolve(expression.expression)

    def visit_if(self, if_statement: stmt.If):
        self._resolve(if_statement.condition)
        self._resolve(if_statement.then_branch)
        if if_statement.else_branch is not None:
            self._resolve(if_statement.else_branch)

    def visit_print(self, print_stmt: stmt.Print):
        self._resolve(print_stmt.expression)

    def visit_return(self, return_stmt: stmt.Return):
        if self._current_function == FunctionType.NONE:
            self._error(return_stmt.keyword, "Can't return from top-level code.")
        if return_stmt.value is not None:
            if self._current_function == FunctionType.INITIALIZER:
                self._error(
                    return_stmt.keyword, "Can't return a value from an initializer."
                )
            self._resolve(return_stmt.value)

    def visit_while(self, while_stmt: stmt.While):
        self._resolve(while_stmt.condition)
        self._resolve(while_stmt.body)

    def visit_class(self, klass: stmt.Class):
        enclosing_class = self._current_class
        self._current_class = ClassType.CLASS
        self._declare(klass.name)
        self._define(klass.name)

        if (
            klass.superclass is not None
            and klass.name.lexeme == klass.superclass.name.lexeme
        ):
            self._error(klass.superclass.name, "A class cannot inherit from itself.")

        if klass.superclass is not None:
            self._current_class = ClassType.SUBCLASS
            self._resolve(klass.superclass)

        if klass.superclass is not None:
            self._begin_scope()
            scope = self._scopes[-1]
            scope["super"] = True
        self._begin_scope()
        scope = self._scopes[-1]
        scope["this"] = True
        for method in klass.methods:
            declaration = FunctionType.METHOD
            if method.name.lexeme == "init":
                declaration = FunctionType.INITIALIZER
            self._resolve_function(method, declaration)

        self._end_scope()
        if klass.superclass is not None:
            self._end_scope()
        self._current_class = enclosing_class

    def visit_super(self, super_expr: expr.Super):
        if self._current_class == ClassType.NONE:
            self._error(super_expr.keyword, "Can't use 'super' outside a class.")
        elif self._current_class != ClassType.SUBCLASS:
            self._error(
                super_expr.keyword,
                "Can't user 'super' in a class with no superclasses.",
            )
        self._resolve_local(super_expr, super_expr.keyword)

    def visit_binary(self, binary: expr.Binary):
        self._resolve(binary.left)
        self._resolve(binary.right)

    def visit_call(self, call_expr: expr.Call):
        self._resolve(call_expr.callee)

        for argument in call_expr.arguments:
            self._resolve(argument)

    def visit_get(self, get_expr: expr.Get):
        self._resolve(get_expr.instance)

    def visit_grouping(self, grouping: expr.Grouping):
        self._resolve(grouping.expression)

    def visit_literal(self, literal: expr.Literal):
        pass

    def visit_logical(self, logical: expr.Logical):
        self._resolve(logical.left)
        self._resolve(logical.right)

    def visit_set(self, set_expr: expr.Set):
        self._resolve(set_expr.value)
        self._resolve(set_expr.instance)

    def visit_this(self, this_expr: expr.This):
        if self._current_class == ClassType.NONE:
            self._error(this_expr.keyword, "Can't use 'this' outside a class.")
            return
        self._resolve_local(this_expr, this_expr.keyword)

    def visit_unary(self, unary: expr.Unary):
        self._resolve(unary.right)

    def _resolve(self, statements: list[typing.Any] | typing.Any):
        if not isinstance(statements, list):
            statements = [statements]
        for statement in statements:
            statement.accept(self)

    def _resolve_local(self, expression: object, name: tokens.Token):
        for i, scope in reversed(list(enumerate(self._scopes))):
            if name.lexeme in scope:
                self._interpreter.resolve(expression, len(self._scopes) - 1 - i)
                return

    def _resolve_function(self, function: stmt.Function, type: FunctionType):
        enclosing_function = self._current_function
        self._current_function = type
        self._begin_scope()
        for param in function.params:
            self._declare(param)
            self._define(param)

        self._resolve(function.body)
        self._end_scope()
        self._current_function = enclosing_function

    def _begin_scope(self):
        self._scopes.append({})

    def _end_scope(self):
        self._scopes.pop()

    def _declare(self, name: tokens.Token):
        if len(self._scopes) == 0:
            return

        scope = self._scopes[-1]
        if name.lexeme in scope:
            self._error(name, "Already a variable with this name in scope.")
        scope[name.lexeme] = False

    def _define(self, name: tokens.Token):
        if len(self._scopes) == 0:
            return

        scope = self._scopes[-1]
        scope[name.lexeme] = True

    def _error(self, token: tokens.Token, message: str):
        if token.type == tokens.TokenType.EOF:
            errors.report(token.line, " at end", message)
        else:
            errors.report(token.line, f" at '{token.lexeme}'", message)


class FunctionType(enum.Enum):
    NONE = 1
    FUNCTION = 2
    METHOD = 3
    INITIALIZER = 4


class ClassType(enum.Enum):
    NONE = 1
    CLASS = 2
    SUBCLASS = 3
