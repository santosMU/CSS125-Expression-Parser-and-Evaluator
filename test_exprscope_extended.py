"""regression tests for semantics, numeric limits, reports, and command-line use."""

import ast
import contextlib
import io
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import tokenize
import unittest

from exprscope import (
    DEMO_CASES, EvalError, LexError, ParseError, SemanticError,
    build_report, compile_expression, diagnostic, evaluate_source,
    explain, main, recursive_fibonacci, repl, run_demo,
)


class SemanticRegressionTests(unittest.TestCase):
    def test_numeric_and_boolean_semantics(self):
        cases = [
            ('-2 ^ 2', -4), ('(-2) ^ 2', 4), ('2 ^ -3', .125),
            ('10 - 3 - 2', 5), ('20 / 2 / 2', 5.0),
            ('-7 % 3', 2), ('0 ^ 0', 1), ('.5 + 1.', 1.5),
            ('true or false and false', True), ('not (1 < 2)', False),
            ('1 == 1.0', True), ('false != true', True),
            ('if false then 1 / 0 else 7', 7),
            ('false and (1 / 0 > 0)', False), ('true or (1 / 0 > 0)', True),
            ('let x = 10 in (let x = x + 1 in x) + x', 21),
            ('let x = 3 in let y = x * 2 in x + y', 9),
            ('let fact = 2 in fact + fact(3)', 8),
            ('fact(0)', 1), ('fib(0)', 0), ('fib(1)', 1),
            ('fact(5.0)', 120), ('abs(-3)', 3), ('min(4, 2)', 2),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                actual = evaluate_source(source)
                self.assertEqual(actual, expected)
                self.assertIs(type(actual), type(expected))

    def test_static_checks_include_unexecuted_branches(self):
        for source in ['if true then 1 else missing', 'false and missing',
                       'if true then 1 else false', 'if 1 then 2 else 3',
                       '1 == true', 'not 1', '1 and true', 'sqrt(true)',
                       'unknown(1)', 'min(1)', 'fact(1, 2)',
                       'let x = x + 1 in x', '(let x = 1 in x) + x',
                       '1 < 2 < 3', 'not 1 < 2']:
            with self.subTest(source=source):
                with self.assertRaises(SemanticError):
                    evaluate_source(source)

    def test_bindings_do_not_persist_between_inputs(self):
        self.assertEqual(evaluate_source('let x = 4 in x'), 4)
        with self.assertRaises(SemanticError):
            evaluate_source('x')

    def test_malformed_inputs(self):
        for source in ['', ' ', '2 3', '1.2.3', '(1 + 2', '2 +',
                       'let true = 1 in true', 'if true then 1', 'min(1,)',
                       '1e3', '2 + if true then 1 else 2']:
            with self.subTest(source=source):
                with self.assertRaises(ParseError):
                    evaluate_source(source)

    def test_illegal_characters(self):
        for source in ['2 $ 3', '1 & 2', 'λ', '١']:
            with self.subTest(source=source), self.assertRaises(LexError):
                evaluate_source(source)

    def test_numeric_domain_errors(self):
        for source in ['0 ^ -1', '10 % 0', '(-1) ^ .5', 'sqrt(-1)',
                       'fact(-1)', 'fib(1.5)', 'fact(201)', 'fib(201)',
                       '2 ^ 4096', '2 ^ 999999999',
                       '10.0 ^ 400', '(10.0 ^ 200) * (10.0 ^ 200)',
                       'sqrt(2 ^ 2000)', 'fact(2 ^ 2000)']:
            with self.subTest(source=source), self.assertRaises(EvalError):
                evaluate_source(source)

    def test_numeric_boundaries(self):
        self.assertEqual(evaluate_source('fact(200)'), math.factorial(200))
        self.assertEqual(evaluate_source('2 ^ 4095'), 2 ** 4095)
        recursive_fibonacci.cache_clear()
        self.assertEqual(evaluate_source('fib(200)'), 280571172992510140037611932413038677189525)
        self.assertGreater(recursive_fibonacci.cache_info().hits, 0)

    def test_input_limits(self):
        for source in ['1' * 201, ' ' * 10001]:
            with self.subTest(size=len(source)), self.assertRaises(LexError):
                evaluate_source(source)

    def test_deep_inputs_produce_language_errors(self):
        for source in ['(' * 1000 + '1' + ')' * 1000, '+'.join(['1'] * 2000)]:
            with self.subTest(size=len(source)):
                with self.assertRaises((ParseError, SemanticError, EvalError)):
                    evaluate_source(source)
                self.assertIsNotNone(build_report(source).error)


class PresentationTests(unittest.TestCase):
    def test_reports_retain_only_completed_stages(self):
        cases = [('2 $ 3', LexError, False, False, False),
                 ('2 + * 3', ParseError, True, False, False),
                 ('1 + true', SemanticError, True, True, False),
                 ('10 / 0', EvalError, True, True, True)]
        for source, error, tokens, tree, semantics in cases:
            with self.subTest(source=source):
                report = build_report(source)
                self.assertIsInstance(report.error, error)
                self.assertEqual(bool(report.tokens), tokens)
                self.assertEqual(bool(report.ast), tree)
                self.assertEqual(bool(report.semantics), semantics)
                self.assertFalse(report.output)

    def test_trace_shows_short_circuit(self):
        report = build_report('false and (10 / 0 > 1)')
        self.assertIsNone(report.error)
        self.assertIn('Binary and => false', report.trace)
        self.assertNotIn('Binary /', report.trace)
        self.assertEqual(report.output, 'false : Boolean')

    def test_demo_asserts_all_examples(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertTrue(run_demo())
        self.assertEqual(output.getvalue().count('CHECK  PASS'), len(DEMO_CASES))

    def test_lexical_error_caret(self):
        report = build_report('2 +\n\t$')
        self.assertIn('\n    $\n    ^', report.render())

    def test_syntax_tree_precedence(self):
        self.assertEqual(build_report('2 + 3 * 4').ast,
            'Binary(+)\n  Number(2)\n  Binary(*)\n    Number(3)\n    Number(4)')

    def test_cli_success_and_failure_statuses(self):
        for arguments, expected in [(['2 + 3'], 0), (['0 ^ -1'], 1),
                                    (['--explain', '1 + true'], 1),
                                    (['--explain', '2 + 3'], 0)]:
            with self.subTest(arguments=arguments), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(arguments), expected)

    def test_file_mode_continues_after_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'expressions.txt'
            path.write_text('# demonstration\n2 + 3\n0 ^ -1\n6 * 7\n', encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(['--file', str(path)]), 1)
            self.assertIn('42 : Number', output.getvalue())
            self.assertIn('Runtime error', output.getvalue())

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            with contextlib.redirect_stderr(io.StringIO()) as output:
                self.assertEqual(main(['--file', str(Path(directory) / 'missing.txt')]), 1)
            self.assertIn('File error:', output.getvalue())

    def test_repl_recovers_after_failure(self):
        result = subprocess.run([sys.executable, '-B', 'exprscope.py'],
            input='0 ^ -1\n2 + 3\n:quit\n', capture_output=True, text=True,
            cwd=Path(__file__).parent, timeout=10)
        self.assertEqual(result.returncode, 0)
        self.assertIn('Runtime error', result.stdout)
        self.assertIn('5 : Number', result.stdout)
        self.assertNotIn('Traceback', result.stderr)

    def test_comments_and_docstrings_are_lowercase(self):
        for path in Path(__file__).parent.glob('*.py'):
            text = path.read_text(encoding='utf-8')
            for token in tokenize.generate_tokens(io.StringIO(text).readline):
                if token.type == tokenize.COMMENT:
                    self.assertEqual(token.string, token.string.lower(), str(path))
            for node in ast.walk(ast.parse(text)):
                body = getattr(node, 'body', None)
                if isinstance(body, list) and body and isinstance(body[0], ast.Expr):
                    value = body[0].value
                    if isinstance(value, ast.Constant) and isinstance(value.value, str):
                        self.assertEqual(value.value, value.value.lower(), str(path))


if __name__ == '__main__':
    unittest.main(verbosity=2)
