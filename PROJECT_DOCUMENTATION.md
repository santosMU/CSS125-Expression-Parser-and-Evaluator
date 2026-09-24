# ExprScope: A Typed Expression Parser and Evaluator

**Group:** 2  
**Course:** CSS125P — Principles of Programming Languages  
**Implementation:** Python 3.10+, standard library; local browser presentation interface  
**Approval:** proposed title, tools, and implementation; instructor approval must be recorded by the group.

## 1. Introduction

ExprScope turns a textual expression into a typed result through distinct language-processing stages. Its primary purpose is to demonstrate how an expression parser and evaluator works. Arithmetic, comparisons, Boolean logic, local bindings, conditional expressions, and fixed mathematical functions provide enough variety to make syntax and semantics visible.

The system offers an interactive terminal, a graphical presentation window, individual command-line expressions, a batch runner, and a self-checking demonstration. All interfaces use the same core implementation.

## 2. Problem Statement

A calculator that only prints a result hides how that result was obtained. Learners need to distinguish token recognition, grammar, precedence, name resolution, type checking, and execution. They also need to understand why an expression can be grammatically valid but semantically invalid, or well typed but fail at runtime.

ExprScope addresses this by exposing tokens with source positions, an abstract syntax tree (AST), inferred types, an execution trace, and errors classified by processing stage.

## 3. General and Specific Objectives

**General objective:** implement an expression parser and evaluator that demonstrates fundamental PPL concepts through an executable, explainable processing pipeline.

Specific objectives:

1. Recognize keywords, identifiers, numeric and Boolean literals, and operators.
2. Implement an explicit grammar using recursive-descent parsing.
3. Represent precedence and associativity in an AST.
4. Resolve identifiers through lexical environments and check types before execution.
5. Evaluate expressions with conditional and short-circuit behavior.
6. Demonstrate function signatures, parameters, and host-language recursion.
7. Recover from invalid input with useful diagnostics.
8. Provide reproducible normal, error, and boundary tests and a clear live demonstration.

## 4. Programming Language Concepts Applied

| Concept | Implementation | Demonstration |
|---|---|---|
| Paradigms | Expression-oriented language with immutable local bindings; imperative Python scanner/parser control flow | `let x = 5 in x * 2` |
| Lexical analysis | `Lexer.scan`, token kinds, reserved keywords | Inspect tokens for `2 + 3 * 4` |
| Syntax and grammar | `Parser`, recursive descent, complete-input consumption | Reject `2 + * 3` |
| Precedence and associativity | Grammar layers, right-recursive power | Compare `2 + 3 * 4`, `(2 + 3) * 4`, `2 ^ 3 ^ 2` |
| Abstract syntax trees | Eight AST node classes | Inspect `Binary(+)` with a `Binary(*)` subtree |
| Static semantics and types | `SemanticAnalyzer`, `ValueType`, function signatures | Reject `1 + true` before execution |
| Variables, binding, and lexical scope | Chained `TypeEnvironment` and `Environment` | Shadow a local variable without changing its outer binding |
| Control structures | `IfExpr`, short-circuit `and` and `or` | Avoid division by zero in an unselected branch |
| Functions and parameters | Fixed numeric built-ins, eager argument evaluation, arity/type checks | `max(4, 9) + sqrt(16)` |
| Recursion | Recursive factorial and memoized recursive Fibonacci in Python | `fact(5) + fib(6)` |
| Error handling | Lexical, syntax, semantic, and runtime exception classes | Four error examples followed by successful input |

The source language has functional characteristics but is not a full functional language: it does not have user-defined functions, closures, or higher-order functions. Recursion is implemented in the Python built-ins, not defined by ExprScope source code. This distinction is part of the demonstration.

## 5. Language / Program Design

### Keywords and identifiers

Reserved, case-sensitive keywords: `let`, `in`, `if`, `then`, `else`, `true`, `false`, `and`, `or`, `not`.

Identifiers match `[A-Za-z_][A-Za-z0-9_]*`. Keywords cannot be binding names. Function names are ordinary identifiers resolved in a separate fixed function namespace: `let fact = 2 in fact + fact(3)` evaluates to 8. Function names cannot be rebound as callable functions.

### Literals and data types

`Number` includes Python integers and finite binary floating-point values. Decimal numeric literals accept `10`, `3.14`, `.5`, and `1.`. Signs are unary operators. Scientific notation, hexadecimal, strings, lists, and complex values are not supported. Only ASCII digits are accepted.

`Boolean` contains `true` and `false`. It is distinct from Number: Python's underlying relationship between `bool` and `int` is not used as a source-language coercion rule. `1 == true` is a semantic error; `1 == 1.0` is valid because both operands have language type Number.

Floating-point arithmetic has normal binary rounding behavior; exact decimal arithmetic is not promised.

### Operators, statements, and expressions

Arithmetic: `+ - * / % ^`. Comparison: `< <= > >=`. Equality: `== !=`. Boolean: `and or not`.

Every source input is one expression that returns a value. There are no assignment statements, loops, semicolons, persistent declarations, or user-defined procedures. `=` only introduces a `let` binding; `==` tests equality. An expression evaluates in a fresh environment. File mode evaluates each nonempty, non-comment line independently. Lines beginning with `#` are file-runner comments, not part of the expression grammar.

## 6. Grammar / Syntax Rules

The following EBNF uses `{ ... }` for repetition and `[ ... ]` for an optional component. `NUMBER` and `IDENT` are token categories. Whitespace separates tokens and is ignored.

```text
program         -> expression EOF ;
expression      -> let_expr | if_expr | or_expr ;
let_expr        -> "let" IDENT "=" expression "in" expression ;
if_expr         -> "if" expression "then" expression "else" expression ;
or_expr         -> and_expr { "or" and_expr } ;
and_expr        -> equality { "and" equality } ;
equality        -> comparison { ("==" | "!=") comparison } ;
comparison      -> additive { ("<" | "<=" | ">" | ">=") additive } ;
additive        -> multiplicative { ("+" | "-") multiplicative } ;
multiplicative  -> unary { ("*" | "/" | "%") unary } ;
unary           -> ("+" | "-" | "not") unary | power ;
power           -> primary [ "^" unary ] ;
primary         -> NUMBER | "true" | "false" | IDENT
                 | IDENT "(" arguments ")" | "(" expression ")" ;
arguments       -> [ expression { "," expression } ] ;
```

Precedence, lowest to highest: `let/if`, `or`, `and`, equality, comparison, addition/subtraction, multiplication/division/modulo, unary operators, power, primary expressions.

Binary operators are left-associative except power, which is right-associative. `2 ^ 3 ^ 2` means `2 ^ (3 ^ 2)` and returns 512. Power binds tighter than unary minus: `-2 ^ 2` returns -4, while `(-2) ^ 2` returns 4. A power exponent accepts unary operators, so `2 ^ -3` returns 0.125.

`not` is a high-precedence unary operator: write `not (1 < 2)`. Comparison chains do not use Python's chained-comparison meaning: `1 < 2 < 3` builds a left-associated tree and fails type checking when a Boolean is compared with a Number. Write `1 < 2 and 2 < 3` instead.

Parentheses are required when a `let` or `if` expression is an arithmetic operand: `2 + (if true then 1 else 2)`. An entire input must be consumed, so trailing tokens are rejected.

## 7. Semantics

Arithmetic and ordering require Number operands. Boolean operators require Boolean operands. Equality requires operands of the same language type. `/` performs true division; `%` follows Python's remainder sign convention, for example `-7 % 3` is 2. `0 ^ 0` is defined as 1. Complex and non-finite results are rejected.

A `let` initializer is evaluated in the enclosing environment. Its body receives a child environment containing the new immutable local binding. Nested bindings can shadow an outer name, but do not mutate it. `let x = x + 1 in x` has no visible outer `x` and is invalid.

An `if` condition must be Boolean; both branches must have the same type. Both branches and both operands of Boolean operators are checked statically. Runtime evaluation executes only the selected branch and short-circuits Boolean operations. Thus `if true then 1 else 1 / 0` is valid and evaluates to 1, but `if true then 1 else missing` is rejected before evaluation.

| Function | Signature | Runtime domain / meaning |
|---|---|---|
| `abs(x)` | Number → Number | Absolute value |
| `sqrt(x)` | Number → Number | Nonnegative input; finite representable floating result |
| `min(a,b)` | Number × Number → Number | Smaller argument |
| `max(a,b)` | Number × Number → Number | Larger argument |
| `fact(n)` | Number → Number | Integer-valued n from 0 through 200; `fact(0)=1` |
| `fib(n)` | Number → Number | Integer-valued n from 0 through 200; `fib(0)=0`, `fib(1)=1` |

Arguments are evaluated eagerly from left to right. Built-ins return values and cannot mutate source bindings. Fibonacci caches recursive subproblem results to avoid exponential repeated work; factorial uses direct recursion. The evaluation trace shows AST-node completions, not each internal Python function call. Recursive implementations can be shown in source during the defense.

## 8. Program Architecture / Flow

```text
GUI / REPL / CLI / file input
            |
            v
     Lexer -> tokens with offsets
            |
            v
     Parser -> abstract syntax tree
            |
            v
     SemanticAnalyzer -> inferred type
            |
            v
     Evaluator -> value and optional trace
            |
            v
     formatted output / stage-specific error
```

`compile_expression` returns tokens, AST, and inferred type. `evaluate_source` runs the pipeline and returns a value. `build_report` runs it once while retaining completed stages and diagnostics. `PipelineReport` supplies the GUI and explanation output. The GUI contains no independent parsing or evaluation logic.

Each failed stage prevents later stages from executing. Runtime reports can retain completed evaluation steps. Lexical and syntax diagnostics include a caret when a token position is available; semantic and runtime errors currently identify the operation or identifier without an exact source span.

## 9. Implementation Details

The lexer uses a regular expression with multi-character operators recognized before their single-character prefixes. The parser maps grammar levels to methods, using loops for left-associative operations and recursion for nested expressions and right-associative exponentiation. Dataclasses represent AST nodes.

The semantic analyzer recursively infers types and uses a separate type environment from the evaluator's value environment. The evaluator traverses the AST, honoring short-circuit behavior before visiting an operand that can be skipped. No Python `eval`, `exec`, or expression-compilation facility processes user expressions.

The GUI uses a standard-library local HTTP server and a browser and provides curated examples, editable source, stage tabs, a full report, and error/status feedback. The local server binds only to 127.0.0.1; the terminal remains usable without a graphical environment.

### Resource and error boundaries

Inputs are limited to 10,000 characters and numeric literals to 200 digits. Integer intermediate results are limited to 4,096 bits. Exponent magnitude is limited to 4,096; obviously oversized integer powers are rejected before computation. Floating-point non-finite values and complex results are rejected. `fact` and `fib` accept at most 200. Excessive expression depth becomes a language error rather than an exposed Python traceback; the exact depth threshold depends on the Python runtime and expression shape.

These explicit limits keep classroom demonstrations responsive. They are design constraints, not claims that mathematical values beyond those limits are invalid. Python numeric overflow and zero-to-negative-power failures are translated into runtime language errors. The REPL continues after language errors and exits cleanly on EOF or Ctrl+C at the input prompt.

## 10. Testing and Results

Run `python -m unittest discover -v`. The suite contains 38 test methods, with additional table-driven subcases covering valid expressions, errors, scope, short-circuiting, input and numeric boundaries, reports, CLI exit statuses, file continuation, and REPL recovery. A source check also verifies lowercase comments and docstrings.

`TEST_RESULTS.txt` contains the captured run. `DEMO_TRANSCRIPT.txt` contains the independently self-checking 12-example walkthrough. Expected error examples count as passing only if the correct exception category is produced.

| Input | Expected outcome | Purpose |
|---|---|---|
| `2 + 3 * 4` | 14 : Number | Precedence |
| `(2 + 3) * 4` | 20 : Number | Grouping |
| `2 ^ 3 ^ 2` | 512 : Number | Right associativity |
| `let x = 10 in (let x = x + 1 in x) + x` | 21 : Number | Scope, initializer binding, shadowing |
| `if 3 < 5 then fact(5) else 10 / 0` | 120 : Number | Selection, recursion, skipped branch |
| `false and (10 / 0 > 1)` | false : Boolean | Short circuit |
| `fact(5) + fib(6)` | 128 : Number | Built-in recursive functions |
| `2 $ 3` | Lexical error | Invalid character |
| `2 + * 3` | Syntax error | Invalid token order |
| `1 + true` | Semantic error | Type mismatch |
| `x + 1` | Semantic error | Missing binding |
| `10 / 0` | Runtime error | Valid types, invalid arithmetic |
| `0 ^ -1` | Runtime error | Host exception containment |

Manual presentation checks: open the GUI, select examples, modify source, press Ctrl+Enter, compare the tree and execution tabs, and confirm a successful expression still works after an error. Browser interaction checks are recorded separately from the automated suite.

## 11. Demonstration Procedure

Use `launch.cmd` or `python exprscope_web.py`. Begin with precedence and parentheses, then show scope and conditional execution, and finish by contrasting error stages. The Next example button advances through all 12 cases. `python exprscope.py --demo` provides a terminal fallback with automatic checks. See `PRESENTATION_GUIDE.md` for the speaking sequence and defense questions.

## 12. Requirements Traceability

| Assignment requirement | Submission evidence |
|---|---|
| Group 2 expression parser and evaluator | Core lexer/parser/evaluator and both interfaces |
| At least five PPL concepts | Section 4 maps eleven concepts to code and examples |
| Input, processing, output, error handling | Sections 7–9 and four diagnostic categories |
| At least three meaningful tests including errors | Section 10, the three test files, captured results |
| Complete readable executable code | Python sources, lowercase comments, README run commands |
| Title, introduction, problem, objectives | Sections 1–3 |
| Language design and lexical elements | Sections 5–7 |
| Grammar and architecture | Sections 6 and 8 |
| Implementation, testing, conclusion, recommendations | Sections 9–10 and 14–15 |
| Instructor approval | Must be obtained and recorded by the group |

## 13. Course Reference Materials

The user supplied lessons on programming-language paradigms, language design criteria, syntax, semantics, lexical/syntax analysis, imperative programming, and functional programming. They are optional course references. This revision is aligned to the assignment text and verified implementation; it does not claim page-level citations or verified quotations from those lesson files.

## 14. Conclusion

ExprScope demonstrates the distinction between recognizing tokens, forming grammatical structure, checking meaning, and computing values. Its examples expose precedence, lexical scope, static typing, recursion, and short-circuit behavior while staying within Group 2's expression-parser-and-evaluator focus. The shared processing pipeline makes results consistent across presentation and terminal interfaces.

## 15. Recommendations and Limitations

Potential extensions include exact source spans for all error categories, a graphical AST diagram, user-defined functions and closures, and additional numeric representations. These would need corresponding grammar, semantic rules, and tests. They are not implemented features. The current project intentionally limits itself to two types, expression-local bindings, fixed built-ins, and bounded computations so the submitted behavior remains explainable and testable.
