import unittest

from exprscope import (
    EvalError,
    LexError,
    ParseError,
    SemanticError,
    evaluate_source,
)


class ExprScopeTests(unittest.TestCase):
    def test_precedence(self):
        self.assertEqual(evaluate_source("2 + 3 * 4"), 14)

    def test_parentheses(self):
        self.assertEqual(evaluate_source("(2 + 3) * 4"), 20)

    def test_right_associative_power(self):
        self.assertEqual(evaluate_source("2 ^ 3 ^ 2"), 512)

    def test_let_binding(self):
        self.assertEqual(evaluate_source("let x = 5 in x * 3"), 15)

    def test_lexical_scope_and_shadowing(self):
        self.assertEqual(
            evaluate_source("let x = 10 in let x = 2 in x + 1"),
            3,
        )

    def test_conditional(self):
        self.assertEqual(
            evaluate_source("if 3 < 5 then 100 else 0"),
            100,
        )

    def test_boolean_logic(self):
        self.assertIs(
            evaluate_source("true and not false"),
            True,
        )

    def test_recursive_functions(self):
        self.assertEqual(evaluate_source("fact(5) + fib(6)"), 128)

    def test_function_call(self):
        self.assertEqual(evaluate_source("max(4, 9) + sqrt(16)"), 13.0)

    def test_type_error(self):
        with self.assertRaises(SemanticError):
            evaluate_source("1 + true")

    def test_undefined_identifier(self):
        with self.assertRaises(SemanticError):
            evaluate_source("x + 1")

    def test_syntax_error(self):
        with self.assertRaises(ParseError):
            evaluate_source("2 + * 3")

    def test_lexical_error(self):
        with self.assertRaises(LexError):
            evaluate_source("2 $ 3")

    def test_division_by_zero(self):
        with self.assertRaises(EvalError):
            evaluate_source("10 / 0")

    def test_function_arity_error(self):
        with self.assertRaises(SemanticError):
            evaluate_source("max(1)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
