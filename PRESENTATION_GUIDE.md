# ExprScope — Live Presentation Guide

## Before presenting

Use Python 3.10+ for the local browser interface. Double-click `launch.cmd`, or run `python exprscope_web.py`. Keep the terminal fallback ready: `python exprscope.py --demo`. Run `python -m unittest discover -v` before the presentation. Obtain instructor approval for the title, Python/browser tools, and scope; approval is not supplied by this project.

## Suggested 7–9 minute sequence

| Time | Action | Explanation |
|---|---|---|
| 0:00–0:45 | Introduce ExprScope | “We are Group 2. Our system parses and evaluates expressions, exposing each PPL processing stage.” |
| 0:45–2:00 | Compare examples 1 and 2; open Tokens and Syntax tree | “The lexer recognizes pieces; the parser organizes them. Parentheses change the tree and the answer from 14 to 20.” |
| 2:00–2:45 | Example 3: power | “Exponentiation is right-associative: 2 raised to 9 is 512.” |
| 2:45–3:45 | Example 4: scope; open Evaluation | “The inner initializer reads outer x=10. Inner x becomes 11, but outer x remains 10, so the answer is 21.” |
| 3:45–4:45 | Examples 5 and 6: selection and short circuit | “Type checking visits both branches; execution visits only the necessary branch or operand. The trace has no division step.” |
| 4:45–5:30 | Example 7: recursion | “The built-ins recursively compute factorial and Fibonacci in Python. Fibonacci reuses computed subproblems.” |
| 5:30–7:00 | Examples 8–12: error stages | “Invalid character, invalid token order, invalid type or name, and invalid runtime arithmetic are different failures.” |
| 7:00–8:00 | Enter a custom valid expression after an error; show test results | “The program recovers. Tests cover successful results and expected failures.” |
| 8:00–9:00 | Summarize scope and answer questions | Explain limits and possible future work without claiming unimplemented features. |

## Interactive challenge inputs

Ask the audience to predict the result before running:

```text
-2 ^ 2
(-2) ^ 2
if true then 1 else 1 / 0
if true then 1 else missing
let x = 10 in (let x = 2 in x) + x
```

Answers: -4, 4, 1, semantic error, 12. The fourth case distinguishes static checking from lazy branch execution.

## Defense questions

**Why not use eval()?** The point is to implement tokenization, grammar, typing, and evaluation ourselves. Input only reaches our own fixed AST operations and numeric built-ins.

**Syntax versus semantics?** `2 + * 3` violates the grammar. `1 + true` follows the grammar but violates the type rules. `10 / 0` is syntactically valid and well typed but fails during execution.

**Where is recursion?** In `recursive_factorial` and `recursive_fibonacci` in `exprscope.py`, and in tree traversal. ExprScope has no user-defined recursive functions. For factorial, explain `fact(5) = 5 × fact(4)` down to the base case 1. Fibonacci memoization avoids repeated subproblem evaluation.

**What paradigm is this?** The source language is expression-oriented with immutable local bindings and functional characteristics. The Python implementation also uses imperative loops and mutable internal token/parser state. It is not a full functional programming language.

**Why is an unused invalid branch rejected?** Static semantics checks the entire tree before runtime selection. A skipped branch may contain a valid operation that would fail at runtime, but it cannot contain an undefined name or incompatible type.

**Are variables permanent?** No. A `let` binds a name within its body. Every new input starts with a fresh environment.

**Does the evaluation trace show recursive call frames?** No. It shows completed AST nodes. Open the recursive functions in source to explain their call structure.

**What are the limitations?** Two types, fixed functions, no mutation or loops in the source language, binary floating-point rounding, and documented resource bounds. A browser is needed only for the presentation interface.

## If something goes wrong live

A language error is a demonstration opportunity: identify its stage and correct the input. If a browser is unavailable, run the terminal demo. File mode intentionally returns a failure exit code when sample error lines are present; this is expected. `DEMO_TRANSCRIPT.txt` records the reproducible guided output as an offline reference.
