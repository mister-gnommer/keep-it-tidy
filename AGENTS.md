# Agent Guidelines for keep-it-tidy

## Maintainer profile

The sole maintainer has deep TypeScript / Node.js expertise and is using this project
to learn Python. They know software engineering well; they are new to Python idioms,
conventions, and the standard library.

## Before acting on requests

**If a request would produce non-idiomatic Python, say so first — then ask whether to
proceed the Pythonic way, the requested way, or explain both.**

Do not silently produce TypeScript-in-disguise. Flag it, explain the Python-native
alternative, and let the maintainer decide.

Common patterns to watch for (things TypeScript developers reach for that Python does
differently):

| Requested pattern | Pythonic alternative |
|---|---|
| Explicit `interface` / structural type | `Protocol` or `TypedDict` from `typing` |
| `enum` with string values used like constants | `enum.Enum` or `enum.StrEnum` |
| `Array.filter / map / reduce` chains | list comprehensions / generator expressions |
| Wrapping everything in a class with static methods | module-level functions |
| `Optional<T>` spelled as `T \| undefined` | `T \| None` / `Optional[T]` |
| `try/catch` for control flow that has a Python idiom | EAFP (`try/except`) is fine, but prefer `if` for simple guards |
| Verbose getter/setter methods | `@property` |
| Index-based `for (let i = 0; ...)` loops | `enumerate()` / `zip()` |
| Explicit `return undefined` | bare `return` or omit entirely |
| Chained ternaries | stay flat; Python ternaries are one level only |
| `console.log` debugging left in | use `logging` module |
| `Promise` / `async` everywhere | only async where I/O actually benefits |
| Named exports and barrel files | Python packages expose via `__init__.py` |

This list is not exhaustive — use judgment. When in doubt: **flag first, act second.**

## General guidance

- Prefer standard-library solutions over third-party packages.
- Follow PEP 8 and PEP 20. When a choice is ambiguous, ask "what would a seasoned
  Python developer reach for?" and prefer that.
- Keep type hints complete; use `mypy --strict` as the bar.
- This project targets Python 3.11+; use modern syntax freely (`match`, `X | Y`
  unions, `tomllib`, etc.).
