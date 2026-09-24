#!/usr/bin/env python3
"""
exprscope
group 2: expression parser and evaluator
css125p - principles of programming languages

processing flow:
source/input -> lexical analysis -> parsing -> semantic analysis
-> evaluation -> output

the implementation uses only the python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
import argparse
from functools import lru_cache
import math
from pathlib import Path
import sys
import re
from typing import Any, Callable, Dict, List, Optional


# ============================================================
# errors
# ============================================================

class ExprScopeError(Exception):
    """base class for user-facing language errors."""


MAX_SOURCE_LENGTH = 10000
MAX_NUMBER_DIGITS = 200
MAX_INTEGER_BITS = 4096
MAX_EXPONENT = 4096


def checked_number(value):
    """keep every intermediate value inside the documented numeric domain."""
    if isinstance(value, int) and not isinstance(value, bool):
        if value.bit_length() > MAX_INTEGER_BITS:
            raise EvalError("Integer result exceeds the 4096-bit limit.")
    elif isinstance(value, float) and not math.isfinite(value):
        raise EvalError("Numeric result must be finite.")
    elif isinstance(value, complex):
        raise EvalError("Expression produced a complex number.")
    return value


class LexError(ExprScopeError):
    pass


class ParseError(ExprScopeError):
    pass


class SemanticError(ExprScopeError):
    pass


class EvalError(ExprScopeError):
    pass


# ============================================================
# tokens and lexical analysis
# ============================================================

class TokenType(Enum):
    NUMBER = auto()
    IDENT = auto()

    LET = auto()
    IN = auto()
    IF = auto()
    THEN = auto()
    ELSE = auto()
    TRUE = auto()
    FALSE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    CARET = auto()

    EQEQ = auto()
    NEQ = auto()
    LT = auto()
    LTE = auto()
    GT = auto()
    GTE = auto()
    ASSIGN = auto()

    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    position: int
    literal: Any = None

    def __str__(self) -> str:
        if self.literal is not None:
            return f"{self.type.name}({format_value(self.literal)})"
        return f"{self.type.name}({self.lexeme!r})"


KEYWORDS = {
    "let": TokenType.LET,
    "in": TokenType.IN,
    "if": TokenType.IF,
    "then": TokenType.THEN,
    "else": TokenType.ELSE,
    "true": TokenType.TRUE,
    "false": TokenType.FALSE,
    "and": TokenType.AND,
    "or": TokenType.OR,
    "not": TokenType.NOT,
}


class Lexer:
    """
    scanner / lexical analyzer.

    converts characters into tokens such as number, ident, plus, let,
    and relational operators. whitespace is ignored.
    """

    _token_pattern = re.compile(
        r"""
        (?P<WS>\s+)
      | (?P<NUMBER>(?:[0-9]+\.[0-9]*|\.[0-9]+|[0-9]+))
      | (?P<IDENT>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<EQEQ>==)
      | (?P<NEQ>!=)
      | (?P<LTE><=)
      | (?P<GTE>>=)
      | (?P<PLUS>\+)
      | (?P<MINUS>-)
      | (?P<STAR>\*)
      | (?P<SLASH>/)
      | (?P<PERCENT>%)
      | (?P<CARET>\^)
      | (?P<LT><)
      | (?P<GT>>)
      | (?P<ASSIGN>=)
      | (?P<LPAREN>\()
      | (?P<RPAREN>\))
      | (?P<COMMA>,)
        """,
        re.VERBOSE,
    )

    def __init__(self, source: str):
        self.source = source

    def scan(self) -> List[Token]:
        if len(self.source) > MAX_SOURCE_LENGTH:
            raise LexError("Input exceeds the 10000-character limit.")
        tokens: List[Token] = []
        pos = 0

        while pos < len(self.source):
            match = self._token_pattern.match(self.source, pos)
            if not match:
                bad = self.source[pos]
                raise LexError(
                    f"Unexpected character {bad!r} at position {pos}."
                )

            kind = match.lastgroup
            lexeme = match.group()
            start = match.start()
            pos = match.end()

            if kind == "WS":
                continue

            if kind == "NUMBER":
                if len(lexeme.replace(".", "")) > MAX_NUMBER_DIGITS:
                    raise LexError(f"Number exceeds 200 digits at position {start}.")
                value = float(lexeme) if "." in lexeme else int(lexeme)
                if isinstance(value, float) and not math.isfinite(value):
                    raise LexError(f"Number must be finite at position {start}.")
                tokens.append(Token(TokenType.NUMBER, lexeme, start, value))
                continue

            if kind == "IDENT":
                token_type = KEYWORDS.get(lexeme, TokenType.IDENT)
                if token_type == TokenType.TRUE:
                    tokens.append(Token(token_type, lexeme, start, True))
                elif token_type == TokenType.FALSE:
                    tokens.append(Token(token_type, lexeme, start, False))
                else:
                    tokens.append(Token(token_type, lexeme, start))
                continue

            tokens.append(Token(TokenType[kind], lexeme, start))

        tokens.append(Token(TokenType.EOF, "", len(self.source)))
        return tokens


# ============================================================
# abstract syntax tree
# ============================================================

class Expr:
    pass


@dataclass
class NumberExpr(Expr):
    value: int | float


@dataclass
class BoolExpr(Expr):
    value: bool


@dataclass
class VariableExpr(Expr):
    name: str


@dataclass
class UnaryExpr(Expr):
    operator: str
    operand: Expr


@dataclass
class BinaryExpr(Expr):
    left: Expr
    operator: str
    right: Expr


@dataclass
class LetExpr(Expr):
    name: str
    value_expr: Expr
    body_expr: Expr


@dataclass
class IfExpr(Expr):
    condition: Expr
    then_expr: Expr
    else_expr: Expr


@dataclass
class CallExpr(Expr):
    name: str
    arguments: List[Expr]


# ============================================================
# recursive-descent parser
# ============================================================

class Parser:
    """
    top-down recursive-descent parser.

    grammar:

    expression      -> let_expr | if_expr | or_expr ;
    let_expr        -> "let" ident "=" expression "in" expression ;
    if_expr         -> "if" expression "then" expression "else" expression ;
    or_expr         -> and_expr { "or" and_expr } ;
    and_expr        -> equality { "and" equality } ;
    equality        -> comparison { ("==" | "!=") comparison } ;
    comparison      -> additive { ("<" | "<=" | ">" | ">=") additive } ;
    additive        -> multiplicative { ("+" | "-") multiplicative } ;
    multiplicative  -> unary { ("*" | "/" | "%") unary } ;
    unary           -> ("+" | "-" | "not") unary | power ;
    power           -> primary [ "^" unary ] ;
    primary         -> number
                     | "true"
                     | "false"
                     | ident
                     | ident "(" arguments ")"
                     | "(" expression ")" ;
    arguments       -> [ expression { "," expression } ] ;

    notes:
    - most binary operators are left-associative.
    - exponentiation is right-associative.
    - grammar layers encode operator precedence.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Expr:
        expr = self.expression()
        self.consume(TokenType.EOF, "Expected end of input.")
        return expr

    def expression(self) -> Expr:
        if self.check(TokenType.LET):
            return self.let_expr()
        if self.check(TokenType.IF):
            return self.if_expr()
        return self.or_expr()

    def let_expr(self) -> Expr:
        self.consume(TokenType.LET, "Expected 'let'.")
        name = self.consume(TokenType.IDENT, "Expected identifier after 'let'.")
        self.consume(TokenType.ASSIGN, "Expected '=' after identifier.")
        value = self.expression()
        self.consume(TokenType.IN, "Expected 'in' after bound expression.")
        body = self.expression()
        return LetExpr(name.lexeme, value, body)

    def if_expr(self) -> Expr:
        self.consume(TokenType.IF, "Expected 'if'.")
        condition = self.expression()
        self.consume(TokenType.THEN, "Expected 'then' after condition.")
        then_expr = self.expression()
        self.consume(TokenType.ELSE, "Expected 'else' after then-expression.")
        else_expr = self.expression()
        return IfExpr(condition, then_expr, else_expr)

    def or_expr(self) -> Expr:
        expr = self.and_expr()
        while self.match(TokenType.OR):
            expr = BinaryExpr(expr, "or", self.and_expr())
        return expr

    def and_expr(self) -> Expr:
        expr = self.equality()
        while self.match(TokenType.AND):
            expr = BinaryExpr(expr, "and", self.equality())
        return expr

    def equality(self) -> Expr:
        expr = self.comparison()
        while self.match(TokenType.EQEQ, TokenType.NEQ):
            op = self.previous().lexeme
            expr = BinaryExpr(expr, op, self.comparison())
        return expr

    def comparison(self) -> Expr:
        expr = self.additive()
        while self.match(TokenType.LT, TokenType.LTE, TokenType.GT, TokenType.GTE):
            op = self.previous().lexeme
            expr = BinaryExpr(expr, op, self.additive())
        return expr

    def additive(self) -> Expr:
        expr = self.multiplicative()
        while self.match(TokenType.PLUS, TokenType.MINUS):
            op = self.previous().lexeme
            expr = BinaryExpr(expr, op, self.multiplicative())
        return expr

    def multiplicative(self) -> Expr:
        expr = self.unary()
        while self.match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.previous().lexeme
            expr = BinaryExpr(expr, op, self.unary())
        return expr

    def unary(self) -> Expr:
        if self.match(TokenType.PLUS, TokenType.MINUS, TokenType.NOT):
            op = self.previous().lexeme
            return UnaryExpr(op, self.unary())
        return self.power()

    def power(self) -> Expr:
        expr = self.primary()
        if self.match(TokenType.CARET):
            expr = BinaryExpr(expr, "^", self.unary())
        return expr

    def primary(self) -> Expr:
        if self.match(TokenType.NUMBER):
            return NumberExpr(self.previous().literal)

        if self.match(TokenType.TRUE, TokenType.FALSE):
            return BoolExpr(self.previous().literal)

        if self.match(TokenType.IDENT):
            name = self.previous().lexeme
            if self.match(TokenType.LPAREN):
                args: List[Expr] = []
                if not self.check(TokenType.RPAREN):
                    args.append(self.expression())
                    while self.match(TokenType.COMMA):
                        args.append(self.expression())
                self.consume(TokenType.RPAREN, "Expected ')' after arguments.")
                return CallExpr(name, args)
            return VariableExpr(name)

        if self.match(TokenType.LPAREN):
            expr = self.expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression.")
            return expr

        token = self.peek()
        raise ParseError(
            f"Expected expression at position {token.position}, "
            f"found {token.lexeme!r}."
        )

    def match(self, *types: TokenType) -> bool:
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def check(self, token_type: TokenType) -> bool:
        return self.peek().type == token_type

    def advance(self) -> Token:
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        return self.tokens[self.current]

    def previous(self) -> Token:
        return self.tokens[self.current - 1]

    def consume(self, token_type: TokenType, message: str) -> Token:
        if self.check(token_type):
            return self.advance()
        token = self.peek()
        raise ParseError(
            f"{message} At position {token.position}, found {token.lexeme!r}."
        )


# ============================================================
# semantic analysis and type checking
# ============================================================

class ValueType(Enum):
    NUMBER = "Number"
    BOOLEAN = "Boolean"


class TypeEnvironment:
    """lexically scoped type environment / symbol table."""

    def __init__(self, parent: Optional["TypeEnvironment"] = None):
        self.parent = parent
        self.symbols: Dict[str, ValueType] = {}

    def define(self, name: str, value_type: ValueType) -> None:
        self.symbols[name] = value_type

    def lookup(self, name: str) -> ValueType:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        raise SemanticError(f"Undefined identifier '{name}'.")


@dataclass(frozen=True)
class FunctionSignature:
    arg_types: tuple[ValueType, ...]
    return_type: ValueType


FUNCTION_SIGNATURES: Dict[str, FunctionSignature] = {
    "abs": FunctionSignature((ValueType.NUMBER,), ValueType.NUMBER),
    "sqrt": FunctionSignature((ValueType.NUMBER,), ValueType.NUMBER),
    "min": FunctionSignature((ValueType.NUMBER, ValueType.NUMBER), ValueType.NUMBER),
    "max": FunctionSignature((ValueType.NUMBER, ValueType.NUMBER), ValueType.NUMBER),
    "fact": FunctionSignature((ValueType.NUMBER,), ValueType.NUMBER),
    "fib": FunctionSignature((ValueType.NUMBER,), ValueType.NUMBER),
}


class SemanticAnalyzer:
    """
    performs static semantic checks before evaluation:
    - identifier resolution
    - lexical scope
    - operand type checking
    - function existence
    - function arity and argument type checking
    - branch type compatibility
    """

    def analyze(self, expr: Expr, env: Optional[TypeEnvironment] = None) -> ValueType:
        env = env or TypeEnvironment()

        if isinstance(expr, NumberExpr):
            return ValueType.NUMBER

        if isinstance(expr, BoolExpr):
            return ValueType.BOOLEAN

        if isinstance(expr, VariableExpr):
            return env.lookup(expr.name)

        if isinstance(expr, UnaryExpr):
            operand_type = self.analyze(expr.operand, env)
            if expr.operator in ("+", "-"):
                self.require(
                    operand_type == ValueType.NUMBER,
                    f"Unary '{expr.operator}' requires a Number."
                )
                return ValueType.NUMBER
            if expr.operator == "not":
                self.require(
                    operand_type == ValueType.BOOLEAN,
                    "'not' requires a Boolean."
                )
                return ValueType.BOOLEAN

        if isinstance(expr, BinaryExpr):
            left_type = self.analyze(expr.left, env)
            right_type = self.analyze(expr.right, env)
            op = expr.operator

            if op in {"+", "-", "*", "/", "%", "^"}:
                self.require(
                    left_type == right_type == ValueType.NUMBER,
                    f"Operator '{op}' requires Number operands."
                )
                return ValueType.NUMBER

            if op in {"<", "<=", ">", ">="}:
                self.require(
                    left_type == right_type == ValueType.NUMBER,
                    f"Operator '{op}' requires Number operands."
                )
                return ValueType.BOOLEAN

            if op in {"==", "!="}:
                self.require(
                    left_type == right_type,
                    f"Operator '{op}' requires operands of the same type."
                )
                return ValueType.BOOLEAN

            if op in {"and", "or"}:
                self.require(
                    left_type == right_type == ValueType.BOOLEAN,
                    f"Operator '{op}' requires Boolean operands."
                )
                return ValueType.BOOLEAN

        if isinstance(expr, LetExpr):
            value_type = self.analyze(expr.value_expr, env)
            local_env = TypeEnvironment(parent=env)
            local_env.define(expr.name, value_type)
            return self.analyze(expr.body_expr, local_env)

        if isinstance(expr, IfExpr):
            condition_type = self.analyze(expr.condition, env)
            self.require(
                condition_type == ValueType.BOOLEAN,
                "The condition of an 'if' expression must be Boolean."
            )
            then_type = self.analyze(expr.then_expr, env)
            else_type = self.analyze(expr.else_expr, env)
            self.require(
                then_type == else_type,
                "The 'then' and 'else' branches must have the same type."
            )
            return then_type

        if isinstance(expr, CallExpr):
            signature = FUNCTION_SIGNATURES.get(expr.name)
            if signature is None:
                raise SemanticError(f"Unknown function '{expr.name}'.")

            if len(expr.arguments) != len(signature.arg_types):
                raise SemanticError(
                    f"Function '{expr.name}' expects {len(signature.arg_types)} "
                    f"argument(s), received {len(expr.arguments)}."
                )

            for index, (argument, expected_type) in enumerate(
                zip(expr.arguments, signature.arg_types), start=1
            ):
                actual_type = self.analyze(argument, env)
                self.require(
                    actual_type == expected_type,
                    f"Argument {index} of '{expr.name}' must be "
                    f"{expected_type.value}, got {actual_type.value}."
                )

            return signature.return_type

        raise SemanticError("Unknown AST node during semantic analysis.")

    @staticmethod
    def require(condition: bool, message: str) -> None:
        if not condition:
            raise SemanticError(message)


# ============================================================
# evaluation
# ============================================================

class Environment:
    """runtime environment implementing lexical scoping."""

    def __init__(self, parent: Optional["Environment"] = None):
        self.parent = parent
        self.values: Dict[str, Any] = {}

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def lookup(self, name: str) -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.lookup(name)
        raise EvalError(f"Undefined identifier '{name}'.")


def _require_nonnegative_integer(value: int | float, function_name: str) -> int:
    if isinstance(value, bool) or (isinstance(value, float) and not value.is_integer()) or value < 0:
        raise EvalError(
            f"{function_name} requires a non-negative integer argument."
        )
    return int(value)


def recursive_factorial(n: int) -> int:
    if n <= 1:
        return 1
    return n * recursive_factorial(n - 1)


@lru_cache(maxsize=201)
def recursive_fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return recursive_fibonacci(n - 1) + recursive_fibonacci(n - 2)


def function_abs(x: int | float) -> int | float:
    return abs(x)


def function_sqrt(x: int | float) -> float:
    if x < 0:
        raise EvalError("sqrt requires a non-negative number.")
    return math.sqrt(x)


def function_min(a: int | float, b: int | float) -> int | float:
    return min(a, b)


def function_max(a: int | float, b: int | float) -> int | float:
    return max(a, b)


def function_fact(x: int | float) -> int:
    n = _require_nonnegative_integer(x, "fact")
    if n > 200:
        raise EvalError("fact argument is limited to 200 for this recursive demo.")
    return recursive_factorial(n)


def function_fib(x: int | float) -> int:
    n = _require_nonnegative_integer(x, "fib")
    if n > 200:
        raise EvalError("fib argument is limited to 200 for this recursive demo.")
    return recursive_fibonacci(n)


FUNCTIONS: Dict[str, Callable[..., Any]] = {
    "abs": function_abs,
    "sqrt": function_sqrt,
    "min": function_min,
    "max": function_max,
    "fact": function_fact,
    "fib": function_fib,
}


class Evaluator:
    def __init__(self, trace: Optional[List[str]] = None):
        self.trace = trace

    def evaluate(self, expr: Expr, env: Optional[Environment] = None) -> Any:
        try:
            value = checked_number(self._evaluate(expr, env))
        except RecursionError as exc:
            raise EvalError("Expression is too deeply nested to evaluate.") from exc
        except (OverflowError, ZeroDivisionError, ValueError) as exc:
            raise EvalError(f"Numeric operation failed: {exc}") from exc
        if self.trace is not None:
            label = type(expr).__name__.removesuffix("Expr")
            detail = getattr(expr, "operator", getattr(expr, "name", ""))
            self.trace.append(f"{label + (' ' + detail if detail else '')} => {format_value(value)}")
        return value

    def _evaluate(self, expr: Expr, env: Optional[Environment] = None) -> Any:
        env = env or Environment()

        if isinstance(expr, NumberExpr):
            return expr.value

        if isinstance(expr, BoolExpr):
            return expr.value

        if isinstance(expr, VariableExpr):
            return env.lookup(expr.name)

        if isinstance(expr, UnaryExpr):
            value = self.evaluate(expr.operand, env)
            if expr.operator == "+":
                return +value
            if expr.operator == "-":
                return -value
            if expr.operator == "not":
                return not value

        if isinstance(expr, BinaryExpr):
            # short-circuit semantics for boolean operators
            if expr.operator == "and":
                left = self.evaluate(expr.left, env)
                return left and self.evaluate(expr.right, env)
            if expr.operator == "or":
                left = self.evaluate(expr.left, env)
                return left or self.evaluate(expr.right, env)

            left = self.evaluate(expr.left, env)
            right = self.evaluate(expr.right, env)
            op = expr.operator

            try:
                if op == "+":
                    return left + right
                if op == "-":
                    return left - right
                if op == "*":
                    return left * right
                if op == "/":
                    if right == 0:
                        raise EvalError("Division by zero.")
                    return left / right
                if op == "%":
                    if right == 0:
                        raise EvalError("Modulo by zero.")
                    return left % right
                if op == "^":
                    if abs(right) > MAX_EXPONENT:
                        raise EvalError("Exponent magnitude exceeds the 4096 limit.")
                    if isinstance(left, int) and isinstance(right, int) and right > 0:
                        if abs(left) > 1 and (abs(left).bit_length() - 1) * right >= MAX_INTEGER_BITS:
                            raise EvalError("Power would exceed the 4096-bit integer limit.")
                    result = left ** right
                    if isinstance(result, complex):
                        raise EvalError("Expression produced a complex number.")
                    return result
                if op == "==":
                    return left == right
                if op == "!=":
                    return left != right
                if op == "<":
                    return left < right
                if op == "<=":
                    return left <= right
                if op == ">":
                    return left > right
                if op == ">=":
                    return left >= right
            except OverflowError as exc:
                raise EvalError(f"Numeric overflow: {exc}") from exc

        if isinstance(expr, LetExpr):
            value = self.evaluate(expr.value_expr, env)
            local_env = Environment(parent=env)
            local_env.define(expr.name, value)
            return self.evaluate(expr.body_expr, local_env)

        if isinstance(expr, IfExpr):
            condition = self.evaluate(expr.condition, env)
            branch = expr.then_expr if condition else expr.else_expr
            return self.evaluate(branch, env)

        if isinstance(expr, CallExpr):
            function = FUNCTIONS.get(expr.name)
            if function is None:
                raise EvalError(f"Unknown function '{expr.name}'.")
            args = [self.evaluate(arg, env) for arg in expr.arguments]
            return function(*args)

        raise EvalError("Unknown AST node during evaluation.")


# ============================================================
# ast formatting and public api
# ============================================================

def format_ast(expr: Expr, indent: str = "") -> str:
    """returns a readable tree representation of the ast."""
    next_indent = indent + "  "

    if isinstance(expr, NumberExpr):
        return f"{indent}Number({expr.value})"

    if isinstance(expr, BoolExpr):
        return f"{indent}Boolean({str(expr.value).lower()})"

    if isinstance(expr, VariableExpr):
        return f"{indent}Variable({expr.name})"

    if isinstance(expr, UnaryExpr):
        return "\n".join([
            f"{indent}Unary({expr.operator})",
            format_ast(expr.operand, next_indent),
        ])

    if isinstance(expr, BinaryExpr):
        return "\n".join([
            f"{indent}Binary({expr.operator})",
            format_ast(expr.left, next_indent),
            format_ast(expr.right, next_indent),
        ])

    if isinstance(expr, LetExpr):
        return "\n".join([
            f"{indent}Let({expr.name})",
            f"{next_indent}Value:",
            format_ast(expr.value_expr, next_indent + "  "),
            f"{next_indent}Body:",
            format_ast(expr.body_expr, next_indent + "  "),
        ])

    if isinstance(expr, IfExpr):
        return "\n".join([
            f"{indent}If",
            f"{next_indent}Condition:",
            format_ast(expr.condition, next_indent + "  "),
            f"{next_indent}Then:",
            format_ast(expr.then_expr, next_indent + "  "),
            f"{next_indent}Else:",
            format_ast(expr.else_expr, next_indent + "  "),
        ])

    if isinstance(expr, CallExpr):
        lines = [f"{indent}Call({expr.name})"]
        for arg in expr.arguments:
            lines.append(format_ast(arg, next_indent))
        return "\n".join(lines)

    return f"{indent}<unknown>"


def compile_expression(source: str) -> tuple[List[Token], Expr, ValueType]:
    """runs lexical analysis, parsing, and semantic analysis."""
    tokens = Lexer(source).scan()
    try:
        ast = Parser(tokens).parse()
    except RecursionError as exc:
        raise ParseError("Expression is too deeply nested to parse.") from exc
    try:
        result_type = SemanticAnalyzer().analyze(ast)
    except RecursionError as exc:
        raise SemanticError("Expression is too deeply nested to analyze.") from exc
    return tokens, ast, result_type


def evaluate_source(source: str) -> Any:
    """runs the complete processing pipeline and returns the result."""
    _, ast, _ = compile_expression(source)
    return Evaluator().evaluate(ast)


def format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


# ============================================================
# interactive demonstration
# ============================================================

HELP_TEXT = """
ExprScope | Group 2 - Expression Parser and Evaluator
  :help                 Show commands
  :tokens <expression>  Show tokens and source positions
  :ast <expression>     Show the abstract syntax tree
  :type <expression>    Show the inferred type
  :explain <expression> Show every processing stage and evaluation trace
  :demo                 Run the guided, self-checking presentation
  :quit                 Exit

Try: let x = 5 in if x > 3 then fact(x) else 0
Bindings are local to one expression. Use parentheses around nested let/if
expressions when using them as arithmetic operands.
""".strip()


def error_stage(error: ExprScopeError) -> str:
    return {LexError: "Lexical", ParseError: "Syntax",
            SemanticError: "Semantic", EvalError: "Runtime"}.get(type(error), "Language")


def diagnostic(source: str, error: ExprScopeError) -> str:
    """show a source caret when the lexer or parser supplies a position."""
    message = f"{error_stage(error)} error: {error}"
    match = re.search(r"position (\d+)", str(error))
    if match:
        position = int(match.group(1))
        line_start = source.rfind("\n", 0, position) + 1
        line_end = source.find("\n", position)
        if line_end < 0:
            line_end = len(source)
        line = source[line_start:line_end].expandtabs(4)
        column = len(source[line_start:position].expandtabs(4))
        message += f"\n{line}\n{' ' * column}^"
    return message


@dataclass
class PipelineReport:
    source: str
    tokens: str = ""
    ast: str = ""
    semantics: str = ""
    trace: str = ""
    output: str = ""
    error: Optional[ExprScopeError] = None

    def render(self) -> str:
        lines = [f"SOURCE  {self.source}"]
        for label, value in [("LEXER", self.tokens), ("AST", self.ast),
                             ("SEMANTICS", self.semantics), ("EVALUATION", self.trace),
                             ("OUTPUT", self.output)]:
            if value:
                lines.append(f"{label}\n{value}")
        if self.error:
            lines.append(diagnostic(self.source, self.error))
        return "\n".join(lines)


def build_report(source: str) -> PipelineReport:
    """execute once and retain completed stages, even when a later stage fails."""
    report = PipelineReport(source)
    stage_error = ParseError
    try:
        tokens = Lexer(source).scan()
        report.tokens = "\n".join(
            f"{t.position:>4}  {t.type.name:<10} {t.lexeme!r}" for t in tokens)
        tree = Parser(tokens).parse()
        report.ast = format_ast(tree)
        stage_error = SemanticError
        result_type = SemanticAnalyzer().analyze(tree)
        report.semantics = f"Valid; inferred type: {result_type.value}"
        trace: List[str] = []
        stage_error = EvalError
        try:
            result = Evaluator(trace).evaluate(tree)
        finally:
            report.trace = "\n".join(trace)
        report.output = f"{format_value(result)} : {result_type.value}"
    except ExprScopeError as exc:
        report.error = exc
    except RecursionError:
        report.error = stage_error("Expression is too deeply nested for this stage.")
    return report


def explain(source: str) -> str:
    """format a complete pipeline report for the terminal."""
    return build_report(source).render()


DEMO_CASES = [
    ("Precedence", "2 + 3 * 4", 14, "Multiplication forms a subtree before addition."),
    ("Parentheses", "(2 + 3) * 4", 20, "Parentheses change the tree, and therefore the result."),
    ("Associativity", "2 ^ 3 ^ 2", 512, "Power groups to the right: 2 ^ (3 ^ 2)."),
    ("Scope", "let x = 10 in (let x = x + 1 in x) + x", 21,
     "The initializer sees outer x; inner x does not replace outer x."),
    ("Selection", "if 3 < 5 then fact(5) else 10 / 0", 120,
     "Both branches are checked, but only the selected branch executes."),
    ("Short circuit", "false and (10 / 0 > 1)", False,
     "The right operand is well typed but never evaluated."),
    ("Recursion", "fact(5) + fib(6)", 128,
     "Built-ins use host-language recursion; Fibonacci memoizes repeated calls."),
    ("Lexical error", "2 $ 3", LexError, "The character is not a token."),
    ("Syntax error", "2 + * 3", ParseError, "Valid tokens appear in an invalid order."),
    ("Type error", "1 + true", SemanticError, "Valid syntax does not imply valid types."),
    ("Binding error", "x + 1", SemanticError, "An identifier needs a visible local binding."),
    ("Runtime error", "10 / 0", EvalError, "Well-typed arithmetic can still fail at runtime."),
]


def run_demo() -> bool:
    print("EXPRSCOPE | GROUP 2 | GUIDED DEMONSTRATION")
    passed = 0
    for index, (title, source, expected, lesson) in enumerate(DEMO_CASES, 1):
        print(f"\n{'=' * 64}\n{index:02d}. {title}\n{lesson}")
        print(explain(source))
        try:
            result = evaluate_source(source)
            correct = type(result) is type(expected) and result == expected
        except ExprScopeError as exc:
            correct = isinstance(expected, type) and type(exc) is expected
        passed += correct
        print("CHECK  " + ("PASS" if correct else "FAIL"))
    print(f"\nDemonstration checks: {passed}/{len(DEMO_CASES)} passed.")
    return passed == len(DEMO_CASES)


def repl() -> None:
    print(HELP_TEXT)
    while True:
        try:
            source = input("\nexpr> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return
        if not source:
            continue
        if source == ":quit":
            return
        if source == ":help":
            print(HELP_TEXT)
            continue
        if source == ":demo":
            run_demo()
            continue
        command, _, expression = source.partition(" ")
        try:
            if command == ":explain":
                print(explain(expression))
            elif command == ":tokens":
                print(" ".join(f"{t}@{t.position}" for t in Lexer(expression).scan()))
            elif command in (":ast", ":type"):
                _, tree, result_type = compile_expression(expression)
                if command == ":ast":
                    print(format_ast(tree))
                print(f"Type: {result_type.value}")
            elif source.startswith(":"):
                print("Unknown command. Type :help for commands.")
            else:
                _, tree, result_type = compile_expression(source)
                result = Evaluator().evaluate(tree)
                print(f"{format_value(result)} : {result_type.value}")
        except ExprScopeError as exc:
            print(diagnostic(expression if source.startswith(":") else source, exc))
        except RecursionError:
            print("Syntax error: Expression is too deeply nested to display.")
        except KeyboardInterrupt:
            print("Evaluation cancelled.")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="ExprScope: Group 2 expression parser and evaluator")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="run the self-checking guided demo")
    group.add_argument("--explain", metavar="EXPRESSION", help="show the full processing pipeline")
    group.add_argument("--file", type=Path, help="evaluate one expression per line; skip blank and # lines")
    group.add_argument("expression", nargs="?", help="evaluate a quoted expression")
    args = parser.parse_args(argv)
    if args.demo:
        return 0 if run_demo() else 1
    if args.explain is not None:
        report = build_report(args.explain)
        print(report.render())
        return int(report.error is not None)
    if args.file is not None:
        try:
            sources = [(n, line.strip()) for n, line in enumerate(
                args.file.read_text(encoding="utf-8-sig").splitlines(), 1)
                if line.strip() and not line.lstrip().startswith("#")]
        except (OSError, UnicodeError) as exc:
            print(f"File error: {exc}", file=sys.stderr)
            return 1
    elif args.expression is not None:
        sources = [(1, args.expression)]
    else:
        repl()
        return 0
    failed = False
    for line_number, source in sources:
        if args.file is not None:
            print(f"\nLine {line_number}: {source}")
        try:
            _, tree, result_type = compile_expression(source)
            print(f"{format_value(Evaluator().evaluate(tree))} : {result_type.value}")
        except ExprScopeError as exc:
            print(diagnostic(source, exc))
            failed = True
    return int(failed)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nCancelled.")
        sys.exit(130)
