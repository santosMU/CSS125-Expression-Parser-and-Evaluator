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

Use `py -3` instead of `python` if that is your installed Windows launcher. The interactive prompt supports `:help`, `:tokens`, `:ast`, `:type`, `:explain`, `:demo`, and `:quit`. Commands that take expressions need a space before the expression.

The demo treats its expected errors as successful checks. File mode continues after errors and exits with status 1 if any expression failed; `sample_inputs.txt` deliberately includes errors. `--explain` also exits with status 1 for invalid input.

## Submission files

| File | Purpose |
|---|---|
| exprscope.py | Lexer, recursive-descent parser, AST, semantic analyzer, evaluator, CLI |
| exprscope_web.py | Presentation window using the same evaluator |
| presentation.html | Local browser presentation interface |
| launch.cmd | Windows presentation launcher |
| test_exprscope.py | Original functional tests |
| test_exprscope_extended.py | Regression, boundary, presentation, and CLI tests |
| test_exprscope_web.py | Local HTTP server integration tests |
| PROJECT_DOCUMENTATION.md | Required academic documentation and language specification |
| PRESENTATION_GUIDE.md | Live walkthrough, expected answers, and defense questions |
| sample_inputs.txt | Batch examples with valid and invalid inputs |
| TEST_RESULTS.txt | Captured automated test output |
| DEMO_TRANSCRIPT.txt | Captured guided demonstration output |

The implementation never delegates expression parsing or execution to Python `eval()` or `exec()`. Functions are fixed numeric built-ins; users cannot define functions or access Python objects.

**Approval status:** the proposed title, tools, and implementation still require instructor approval; no approval is claimed here.
