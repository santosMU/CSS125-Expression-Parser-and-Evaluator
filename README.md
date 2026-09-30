# ExprScope

**Group 2 · Principles of Programming Languages**  
An expression parser and evaluator with a visible lexer, syntax tree, static type checking, lexical scope, and execution trace.

## Start the presentation

On Windows, double-click **launch.cmd**. It finds the Python launcher, Python on PATH, or the bundled runtime available on this machine. The window includes 12 examples, an editable input, processing-stage tabs, and a Next example button. Use **Ctrl+Enter** to evaluate edited input.

Alternatively:

```console
python exprscope_web.py
```

Requires Python **3.10+**. The GUI also requires the a standard-library local HTTP server and a browser module, normally included with Windows Python. The terminal works without Tk. No pip packages, network connection, or API keys are needed.

## Terminal commands

```console
python exprscope.py
python exprscope.py "let x = 5 in x ^ 2 + 1"
python exprscope.py --explain "2 + 3 * 4"
python exprscope.py --demo
python exprscope.py --file sample_inputs.txt
python -m unittest discover -v
```

## Influencing Frameworks and Related Repositories

Credit goes to the authors and contributors of the following open-source projects for their expression-parsing and evaluation approaches. They are acknowledged here as conceptual influencing frameworks and comparison references for this documentation. This acknowledgment does not establish that they were consulted during the original implementation or that their code was reused.

| Repository and credit | Shared purpose and conceptual influence | Difference from ExprScope |
|---|---|---|
| [TinyExpr](https://github.com/codeplea/tinyexpr), by Code Plea and contributors | Mathematical expression parsing and evaluation through recursive descent; a reference for precedence-aware parsing and a compact evaluation engine. | Implemented in C; ExprScope implements its own Python pipeline with static types, local bindings, and stage reports. |
| [parser-project](https://github.com/achanbour/parser-project), by achanbour and contributors | A Python calculator demonstrating lexical analysis and recursive-descent parsing; a reference for making arithmetic grammar and parsing steps explicit. | Focuses on a calculator model; ExprScope also demonstrates Boolean expressions, lexical scope, and static semantic checking. |
| [simpleeval](https://github.com/danthedeckie/simpleeval), by danthedeckie and contributors | Controlled expression evaluation in Python; a reference for explicit handling of operators, names, and permitted functions. | Uses Python's `ast` module; ExprScope defines its own grammar, lexer, AST, and type checker. |

These repositories address the same core task of parsing and evaluating expressions, but do not provide an identical language or feature set. They are reference projects rather than installed framework dependencies. ExprScope uses the Python standard library and its own implementation.

