# ExprScope

ExprScope is a typed expression parser and evaluator implemented in Python. It exposes tokens, an abstract syntax tree, static types, lexical scope, and execution traces through a CLI and local browser workspace.

## Requirements

Python 3.10+. No third-party packages or API keys are required. The browser interface binds to `127.0.0.1`.

## Usage

```console
python exprscope.py
python exprscope.py "let x = 5 in x ^ 2 + 1"
python exprscope.py --explain "2 + 3 * 4"
python exprscope.py --examples
python exprscope.py --file examples/expressions.txt
python exprscope_web.py
python -m unittest discover -s tests -v
```

On Windows, `launch.cmd` opens the browser workspace. Server options include `--no-browser` and `--port 8766`.

The REPL supports `:help`, `:tokens`, `:ast`, `:type`, `:explain`, `:examples`, and `:quit`. Batch processing continues after errors and returns a nonzero exit status if any expression fails. The supplied batch file includes intentional error cases.

## Features

- Arithmetic and Boolean expressions with explicit precedence and associativity.
- Immutable lexical bindings, conditionals, and short-circuit evaluation.
- Fixed mathematical functions: `abs`, `sqrt`, `min`, `max`, `fact`, and `fib`.
- Lexical, syntax, semantic, and runtime diagnostics.
- Explicit bounds on input and numeric computations.

See the [language reference](docs/language-reference.md) for grammar, semantics, architecture, and limits.

## Repository Layout

| Path | Purpose |
|---|---|
| `exprscope.py` | Lexer, parser, AST, type checker, evaluator, reports, and CLI. |
| `exprscope_web.py` | Local HTTP server and JSON endpoints. |
| `web/index.html` | Browser expression workspace. |
| `docs/language-reference.md` | Language specification and implementation reference. |
| `tests/` | Regression and HTTP integration tests. |
| `examples/expressions.txt` | Valid expressions and expected errors. |
| `launch.cmd` | Windows launcher. |

## Influencing Frameworks and Related Repositories

Credit goes to the authors and contributors of the following open-source projects for their expression-parsing and evaluation approaches. They are acknowledged here as conceptual influencing frameworks and comparison references for this documentation. This acknowledgment does not establish that they were consulted during the original implementation or that their code was reused.

| Repository and credit | Shared purpose and conceptual influence | Difference from ExprScope |
|---|---|---|
| [TinyExpr](https://github.com/codeplea/tinyexpr), by Code Plea and contributors | Mathematical expression parsing and evaluation through recursive descent; a reference for precedence-aware parsing and a compact evaluation engine. | Implemented in C; ExprScope implements its own Python pipeline with static types, local bindings, and stage reports. |
| [parser-project](https://github.com/achanbour/parser-project), by achanbour and contributors | A Python calculator demonstrating lexical analysis and recursive-descent parsing; a reference for making arithmetic grammar and parsing steps explicit. | Focuses on a calculator model; ExprScope also demonstrates Boolean expressions, lexical scope, and static semantic checking. |
| [simpleeval](https://github.com/danthedeckie/simpleeval), by danthedeckie and contributors | Controlled expression evaluation in Python; a reference for explicit handling of operators, names, and permitted functions. | Uses Python's `ast` module; ExprScope defines its own grammar, lexer, AST, and type checker. |

| [Gee](https://github.com/pulanski/gee), by pulanski and contributors | Hand-written lexing, LL(1) recursive-descent parsing, AST construction, and a separate type checker; a conceptual reference for distinct syntax and semantic-analysis stages. | A compiler front-end for the Gee language; ExprScope also evaluates expressions and exposes execution traces. |
| [Pascal-Interpreter](https://github.com/kevallakhani95/Pascal-Interpreter), by kevallakhani95 and contributors | A Python interpreter using a lexer, recursive-descent parser, AST traversal, and symbol-table definition and lookup; a conceptual reference for language-processing structure and identifier resolution. | Processes Pascal programs with declarations and statements; ExprScope evaluates a smaller expression language with immutable local bindings. |

These projects provide related approaches to expression evaluation, interpretation, and compiler front-end analysis. Their languages and feature sets differ from ExprScope. They are conceptual references rather than installed framework dependencies. ExprScope uses the Python standard library and its own implementation.
