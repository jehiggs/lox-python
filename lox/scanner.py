import errors
from tokens import Token, TokenType


class Scanner:
    def __init__(self, source: str):
        """Create a new scanner"""
        self._source = source
        self._tokens: list[Token] = []
        self._current = 0
        self._start = 0
        self._line = 1

    def scan_tokens(self) -> list[Token]:
        while self._current < len(self._source):
            self._start = self._current
            self._scan_token()

        self._tokens.append(Token(TokenType.EOF, "", None, self._line))

        return self._tokens

    def _scan_token(self):
        character = self._advance()
        match character:
            case "(":
                self._add_token(TokenType.LEFT_PARENTHESIS)
            case ")":
                self._add_token(TokenType.RIGHT_PARENTHESIS)
            case "{":
                self._add_token(TokenType.LEFT_BRACE)
            case "}":
                self._add_token(TokenType.RIGHT_BRACE)
            case ",":
                self._add_token(TokenType.COMMA)
            case ".":
                self._add_token(TokenType.DOT)
            case "-":
                self._add_token(TokenType.MINUS)
            case "+":
                self._add_token(TokenType.PLUS)
            case ";":
                self._add_token(TokenType.SEMICOLON)
            case "*":
                self._add_token(TokenType.STAR)
            case "!":
                if self._match("="):
                    self._add_token(TokenType.BANG_EQUAL)
                else:
                    self._add_token(TokenType.BANG)
            case "=":
                if self._match("="):
                    self._add_token(TokenType.EQUAL_EQUAL)
                else:
                    self._add_token(TokenType.EQUAL)
            case "<":
                if self._match("="):
                    self._add_token(TokenType.LESS_EQUAL)
                else:
                    self._add_token(TokenType.LESS)
            case ">":
                if self._match("="):
                    self._add_token(TokenType.GREATER_EQUAL)
                else:
                    self._add_token(TokenType.GREATER)
            case "/":
                if self._match("/"):
                    while self._peek() != "\n" and self._current < len(self._source):
                        self._advance()
                else:
                    self._add_token(TokenType.SLASH)
            case " ":
                pass
            case "\r":
                pass
            case "\t":
                pass
            case "\n":
                self._line += 1
            case '"':
                self._string()

            case _:
                if self._is_digit(character):
                    self._number()
                elif self._is_alpha(character):
                    self._identifier()
                else:
                    errors.report(self._line, "", f"Failed to scan token: {character}")

    def _advance(self) -> str:
        character = self._source[self._current]
        self._current += 1
        return character

    def _add_token(self, type: TokenType, literal: object = None):
        text = self._source[self._start : self._current]
        self._tokens.append(Token(type, text, literal, self._line))

    def _match(self, expected: str) -> bool:
        if self._current >= len(self._source):
            return False
        if self._source[self._current] != expected:
            return False
        self._current += 1
        return True

    def _peek(self) -> str:
        if self._current >= len(self._source):
            return "\0"
        else:
            return self._source[self._current]

    def _string(self):
        while self._peek() != '"' and self._current < len(self._source):
            if self._peek() == "\n":
                self._line += 1
            self._advance()

        if self._current >= len(self._source):
            errors.report(self._line, "", "Unterminated string")

        # Advance past the closing quote.
        self._advance()
        value = self._source[self._start + 1 : self._current - 1]
        self._add_token(TokenType.STRING, value)

    def _is_digit(self, character: str) -> bool:
        return character.isdigit()

    def _number(self):
        while self._is_digit(self._peek()):
            self._advance()

        if self._peek() == "." and self._is_digit(self._peek_next()):
            self._advance()
            while self._is_digit(self._peek()):
                self._advance()

        self._add_token(
            TokenType.NUMBER, float(self._source[self._start : self._current])
        )

    def _peek_next(self) -> str:
        if self._current + 1 >= len(self._source):
            return "\0"
        return self._source[self._current + 1]

    def _is_alpha(self, character: str) -> bool:
        return character.isalpha() or character == "_"

    def _identifier(self):
        while self._is_alpha(self._peek()) or self._is_digit(self._peek()):
            self._advance()

        text = self._source[self._start : self._current]
        type = self.keywords.get(text)
        if type is None:
            type = TokenType.IDENTIFIER
        self._add_token(type)

    keywords = {
        "and": TokenType.AND,
        "class": TokenType.CLASS,
        "else": TokenType.ELSE,
        "false": TokenType.FALSE,
        "for": TokenType.FOR,
        "fun": TokenType.FUN,
        "if": TokenType.IF,
        "nil": TokenType.NIL,
        "or": TokenType.OR,
        "print": TokenType.PRINT,
        "return": TokenType.RETURN,
        "super": TokenType.SUPER,
        "this": TokenType.THIS,
        "true": TokenType.TRUE,
        "var": TokenType.VAR,
        "while": TokenType.WHILE,
    }
