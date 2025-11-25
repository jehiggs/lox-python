# Lox Python

A Python implementation of the first half of [Crafting Interpreters](https://craftinginterpreters.com/a-tree-walk-interpreter.html).

This is pretty much a straight translation of the original Java code. The aim was to follow the book as closely as possible in order to learn a little more about building parsers and interpreters.

The first half of the book runs through a tree walk interpreter. It covers scanning the source code to build tokens, building a recursive descent parser to construct an AST, and then walking the AST in the interpreter to execute the code.

The code quality is relatively low as this was passed through quickly as a learning exercise.

## Running the code

You can run the REPL using [`uv`](https://docs.astral.sh/uv/):

```sh
uv run lox/main.py
```

Alternatively, you can execute one of the examples as follows:

```sh
uv run lox/main.py examples/<lox-file>
```
