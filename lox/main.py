import argparse

import errors
from interpreter import Interpreter
from parser import Parser
from resolver import Resolver
from scanner import Scanner


class Lox:
    def __init__(self):
        self._interpreter = Interpreter()

    def runPrompt(self):
        while True:
            line = input("> ")
            if line:
                self._run(line)
                errors.reset()

    def runFile(self, file: str) -> int:
        with open(file, "r") as f:
            content = f.read()
            self._run(content)
            if errors.is_error():
                return 65
            elif errors.is_runtime_error():
                return 70
            else:
                return 0

    def _run(self, content):
        """Execute a Lox program"""
        scanner = Scanner(content)
        tokens = scanner.scan_tokens()
        parser = Parser(tokens)
        statements = parser.parse()
        if errors.is_error():
            return
        resolver = Resolver(self._interpreter)
        resolver._resolve(statements)
        if errors.is_error():
            return
        self._interpreter.interpret(statements)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="lox", description="Lox interpreter")
    parser.add_argument("file", nargs="?", default=None)
    args = parser.parse_args()
    lox = Lox()
    if args.file:
        lox.runFile(args.file)
    else:
        lox.runPrompt()
