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