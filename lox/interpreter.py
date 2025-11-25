import typing

import environment
import errors
import expr
import loxclass
import loxfunction
import loxinstance
import natives
import return_exception
import stmt
import tokens


class Interpreter:
    def __init__(self):
        self.globals = environment.Environment()
        self._environment = self.globals
        self.globals.define("clock", natives.Clock())
        self._locals = {}

    def interpret(self, statements: list[typing.Any]):
        try:
            for statement in statements:
                self._execute(statement)
        except errors.RuntimeError as e:
            errors.runtime_error(e)

    def visit_literal(self, expression: expr.Literal) -> typing.Any:
        return expression.value

    def visit_get(self, expression: expr.Get) -> typing.Any:
        instance = self._evaluate(expression.instance)
        if isinstance(instance, loxinstance.LoxInstance):
            return instance.get(expression.name)

        raise errors.RuntimeError(expression.name, "Only instances have properties")

    def visit_grouping(self, expression: expr.Grouping) -> typing.Any:
        return self._evaluate(expression.expression)

    def visit_set(self, set_expr: expr.Set) -> typing.Any:
        instance = self._evaluate(set_expr.instance)
        if not isinstance(instance, loxinstance.LoxInstance):
            raise errors.RuntimeError(set_expr.name, "Only instances have fields.")

        value = self._evaluate(set_expr.value)
        instance.set(set_expr.name, value)
        return value

    def visit_unary(self, expression: expr.Unary) -> typing.Any:
        right = self._evaluate(expression)

        match expression.operator.type:
            case tokens.TokenType.MINUS:
                self._check_number_operands(expression.operator, right)
                return -float(right)
            case tokens.TokenType.BANG:
                return not self._is_truthy(right)

        # Should be unreachable.
        return None

    def visit_binary(self, expression: expr.Binary) -> typing.Any:
        left = self._evaluate(expression.left)
        right = self._evaluate(expression.right)

        match expression.operator.type:
            case tokens.TokenType.MINUS:
                self._check_number_operands(expression.operator, left, right)
                return float(left) - float(right)
            case tokens.TokenType.SLASH:
                self._check_number_operands(expression.operator, left, right)
                return float(left) / float(right)
            case tokens.TokenType.STAR:
                self._check_number_operands(expression.operator, left, right)
                return float(left) * float(right)
            case tokens.TokenType.PLUS:
                if isinstance(left, float) and isinstance(right, float):
                    return left + right
                elif isinstance(left, str) and isinstance(right, str):
                    return left + right
                else:
                    raise errors.RuntimeError(
                        expression.operator,
                        "Operands must be two numbers or two strings.",
                    )
            case tokens.TokenType.GREATER:
                self._check_number_operands(expression.operator, left, right)
                return float(left) > float(right)
            case tokens.TokenType.GREATER_EQUAL:
                self._check_number_operands(expression.operator, left, right)
                return float(left) >= float(right)
            case tokens.TokenType.LESS:
                self._check_number_operands(expression.operator, left, right)
                return float(left) < float(right)
            case tokens.TokenType.LESS_EQUAL:
                self._check_number_operands(expression.operator, left, right)
                return float(left) <= float(right)
            case tokens.TokenType.BANG_EQUAL:
                return not self._is_equal(left, right)
            case tokens.TokenType.EQUAL_EQUAL:
                return self._is_equal(left, right)

        # Should be unreachable.
        return None

    def visit_print(self, print_statement: stmt.Print) -> None:
        value = self._evaluate(print_statement.expression)
        print(self._stringify(value))

    def visit_expression(self, expr_statement: stmt.Expression) -> None:
        self._evaluate(expr_statement.expression)

    def visit_var(self, var_statement: stmt.Var) -> None:
        value = None
        if var_statement.initializer is not None:
            value = self._evaluate(var_statement.initializer)

        self._environment.define(var_statement.name.lexeme, value)

    def visit_variable(self, variable: expr.Variable) -> object:
        return self._lookup_variable(variable.name, variable)

    def visit_assign(self, assignment: expr.Assign) -> object:
        value = self._evaluate(assignment.value)
        distance = self._locals.get(assignment)
        if distance is not None:
            self._environment.assign_at(distance, assignment.name, value)
        else:
            self.globals.assign(assignment.name, value)
        return value

    def visit_block(self, block: stmt.Block) -> None:
        self._execute_block(
            block.statements, environment.Environment(self._environment)
        )

    def visit_class(self, klass: stmt.Class):
        superclass = None
        if klass.superclass is not None:
            superclass = self._evaluate(klass.superclass)
            if not isinstance(superclass, loxclass.LoxClass):
                raise errors.RuntimeError(
                    klass.superclass.name, "Superclass must be a class."
                )

        self._environment.define(klass.name.lexeme, None)
        if klass.superclass is not None:
            self._environment = environment.Environment(self._environment)
            self._environment.define("super", superclass)
        methods = {}
        for method in klass.methods:
            function = loxfunction.LoxFunction(
                method, self._environment, method.name.lexeme == "init"
            )
            methods[method.name.lexeme] = function
        class_obj = loxclass.LoxClass(klass.name.lexeme, superclass, methods)
        if superclass is not None:
            self._environment = self._environment._enclosing
        self._environment.assign(klass.name, class_obj)

    def visit_super(self, super_expr: expr.Super):
        distance = self._locals.get(super_expr)
        superclass = self._environment.get_at(distance, "super")
        obj = self._environment.get_at(distance - 1, "this")
        method = superclass.find_method(super_expr.method.lexeme)
        if not method:
            raise errors.RuntimeError(
                super_expr.method, f"Undefined property '{super_expr.method.lexeme}'."
            )
        return method.bind(obj)

    def visit_if(self, if_statement: stmt.If):
        if self._is_truthy(self._evaluate(if_statement.condition)):
            self._execute(if_statement.then_branch)
        elif if_statement.else_branch is not None:
            self._execute(if_statement.else_branch)

    def visit_while(self, while_statement: stmt.While):
        while self._is_truthy(self._evaluate(while_statement.condition)):
            self._execute(while_statement.body)

    def visit_logical(self, logical: expr.Logical):
        left = self._evaluate(logical.left)

        if logical.operator.type == tokens.TokenType.OR:
            if self._is_truthy(left):
                return left
        else:
            if not self._is_truthy(left):
                return left

        return self._evaluate(logical.right)

    def visit_call(self, expression: expr.Call):
        callee = self._evaluate(expression.callee)

        arguments = []
        for argument in expression.arguments:
            arguments.append(self._evaluate(argument))

        if not callable(getattr(callee, "call", None)):
            raise errors.RuntimeError(
                expression.paren, "Can only call functions and classes."
            )

        if callable(getattr(callee, "arity", None)):
            if len(arguments) != callee.arity():
                raise errors.RuntimeError(
                    expression.paren,
                    f"Expected {callee.arity()} arguments but got {len(arguments)}.",
                )
        else:
            raise errors.RuntimeError(expression.paren, "Callable does not have arity.")

        return callee.call(self, arguments)

    def visit_function(self, func_call: stmt.Function):
        function = loxfunction.LoxFunction(func_call, self._environment, False)
        self._environment.define(func_call.name.lexeme, function)

    def visit_return(self, statement: stmt.Return):
        value = None
        if statement.value is not None:
            value = self._evaluate(statement.value)

        raise return_exception.Return(value)

    def visit_this(self, this_expr: expr.This):
        return self._lookup_variable(this_expr.keyword, this_expr)

    def resolve(self, expression: object, depth: int):
        self._locals[expression] = depth

    def _execute(self, statement: typing.Any):
        statement.accept(self)

    def _execute_block(self, statements: list[object], env: environment.Environment):
        prev_env = self._environment
        try:
            self._environment = env

            for statement in statements:
                self._execute(statement)

        finally:
            self._environment = prev_env

    def _evaluate(self, expression: typing.Any) -> typing.Any:
        return expression.accept(self)

    def _is_truthy(self, object: typing.Any) -> bool:
        if object is None:
            return False
        if isinstance(object, bool):
            return object

        return True

    def _is_equal(self, left: typing.Any, right: typing.Any) -> bool:
        if left is None and right is None:
            return True
        if left is None:
            return False
        return left == right

    def _check_number_operands(self, operator: tokens.Token, *operands: typing.Any):
        if all(isinstance(operand, float) for operand in operands):
            return
        raise errors.RuntimeError(operator, "Operands must be numbers.")

    def _stringify(self, value: typing.Any) -> str:
        if value is None:
            return "nil"

        if isinstance(value, float):
            text = str(value)
            if text.endswith(".0"):
                text = text[0:-2]
            return text

        if isinstance(value, bool):
            if value:
                return "true"
            else:
                return "false"

        return str(value)

    def _lookup_variable(self, name: tokens.Token, expression: object):
        distance = self._locals.get(expression)
        if distance is not None:
            return self._environment.get_at(distance, name.lexeme)
        else:
            return self.globals.get(name)
