# ExprScope: A Typed Expression Parser and Evaluator

Implementation reference for Python 3.10+ using the standard library.

## Introduction

ExprScope turns a textual expression into a typed result through distinct language-processing stages. Its primary purpose is to demonstrate how an expression parser and evaluator works. Arithmetic, comparisons, Boolean logic, local bindings, conditional expressions, and fixed mathematical functions provide enough variety to make syntax and semantics visible.

The system offers an interactive terminal, a local browser interface, command-line evaluation, a batch runner, and self-checking examples. All interfaces use the same core implementation.

## Problem Statement

A calculator that only prints a result hides how that result was obtained. Learners need to distinguish token recognition, grammar, precedence, name resolution, type checking, and execution. They also need to understand why an expression can be grammatically valid but semantically invalid, or well typed but fail at runtime.

ExprScope addresses this by exposing tokens with source positions, an abstract syntax tree (AST), inferred types, an execution trace, and errors classified by processing stage.

## General and Specific Objectives

**General objective:** implement an expression parser and evaluator that demonstrates fundamental PPL concepts through an executable, explainable processing pipeline.

Specific objectives:

1. Recognize keywords, identifiers, numeric and Boolean literals, and operators.
2. Implement an explicit grammar using recursive-descent parsing.
3. Represent precedence and associativity in an AST.
4. Resolve identifiers through lexical environments and check types before execution.
5. Evaluate expressions with conditional and short-circuit behavior.
6. Demonstrate function signatures, parameters, and host-language recursion.
7. Recover from invalid input with useful diagnostics.
8. Provide reproducible normal, error, and boundary tests and documented usage examples.

## Programming Language Concepts Applied

| Concept | Implementation | Example |
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

The source language has functional characteristics but is not a full functional language: it does not have user-defined functions, closures, or higher-order functions. Recursion is implemented in the Python built-ins, not defined by ExprScope source code. The distinction separates source-language features from host-language implementation.

## Language / Program Design

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

## Grammar / Syntax Rules

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

## Semantics

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

Arguments are evaluated eagerly from left to right. Built-ins return values and cannot mutate source bindings. Fibonacci caches recursive subproblem results to avoid exponential repeated work; factorial uses direct recursion. The evaluation trace shows AST-node completions, not each internal Python function call. The recursive implementations are defined in `exprscope.py`.

## Program Architecture / Flow

```text
Browser / REPL / CLI / file input
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

`compile_expression` returns tokens, AST, and inferred type. `evaluate_source` runs the pipeline and returns a value. `build_report` runs it once while retaining completed stages and diagnostics. `PipelineReport` supplies the browser interface and explanation output. The browser interface contains no independent parsing or evaluation logic.

Each failed stage prevents later stages from executing. Runtime reports can retain completed evaluation steps. Lexical and syntax diagnostics include a caret when a token position is available; semantic and runtime errors currently identify the operation or identifier without an exact source span.

## Implementation Details

The lexer uses a regular expression with multi-character operators recognized before their single-character prefixes. The parser maps grammar levels to methods, using loops for left-associative operations and recursion for nested expressions and right-associative exponentiation. Dataclasses represent AST nodes.

The semantic analyzer recursively infers types and uses a separate type environment from the evaluator's value environment. The evaluator traverses the AST, honoring short-circuit behavior before visiting an operand that can be skipped. No Python `eval`, `exec`, or expression-compilation facility processes user expressions.

The browser interface uses a standard-library local HTTP server and a browser and provides curated examples, editable source, stage tabs, a full report, and error/status feedback. The local server binds only to 127.0.0.1; the terminal remains usable without a graphical environment.

### Resource and error boundaries

Inputs are limited to 10,000 characters and numeric literals to 200 digits. Integer intermediate results are limited to 4,096 bits. Exponent magnitude is limited to 4,096; obviously oversized integer powers are rejected before computation. Floating-point non-finite values and complex results are rejected. `fact` and `fib` accept at most 200. Excessive expression depth becomes a language error rather than an exposed Python traceback; the exact depth threshold depends on the Python runtime and expression shape.

These explicit limits keep interactive use responsive. They are design constraints, not claims that mathematical values beyond those limits are invalid. Python numeric overflow and zero-to-negative-power failures are translated into runtime language errors. The REPL continues after language errors and exits cleanly on EOF or Ctrl+C at the input prompt.

## Testing and Results

Run `python -m unittest discover -s tests -v` from the repository root. The suite covers valid expressions, diagnostics, scope, short-circuiting, numeric limits, reports, CLI exit statuses, batch processing, REPL recovery, and HTTP endpoints.

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

## Limitations and Future Work

Potential extensions include exact source spans for all error categories, an interactive AST diagram, user-defined functions and closures, and additional numeric representations. These would need corresponding grammar, semantic rules, and tests. They are not implemented features. The current project intentionally limits itself to two types, expression-local bindings, fixed built-ins, and bounded computations to keep behavior explicit and testable.
