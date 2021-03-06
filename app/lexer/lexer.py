import re
from typing import Match, Optional

from . import token

KEYWORD_GROUP = "keyword"
VARIABLE_GROUP = "variable"
WORD_GROUP = "word"
NUMBER_GROUP = "number"
LINE_FEED_GROUP = "line_feed"
WHITESPACES_GROUP = "whitespaces"

KEYWORD = r"\(|\)|@new|@rule|@apply|@and|@or|@not|<|>|\."
VARIABLE = r"\$[a-zA-Z]+[0-9]*"
WORD = r"[a-zA-Z]+[0-9]*"
NUMBER = r"[0-9]+"
LINE_FEED = r"\r?\n"
WHITESPACES = r"[ \f\r\t\v]+"
PATTERN = f"(?P<{KEYWORD_GROUP}>{KEYWORD})|(?P<{VARIABLE_GROUP}>{VARIABLE})|(?P<{WORD_GROUP}>{WORD})|" \
          f"(?P<{NUMBER_GROUP}>{NUMBER})|(?P<{LINE_FEED_GROUP}>{LINE_FEED})|(?P<{WHITESPACES_GROUP}>{WHITESPACES})"
regexp = re.compile(PATTERN)


class Lexer:
    def __init__(self, program: str):
        self._program = program
        self._position = 0
        self._delta = 0
        self._line_num = 1
        self._regexp = regexp
        self._match: Optional[Match[str]] = None

    def _find(self) -> Optional[Match[str]]:
        return self._regexp.match(self._program, pos=self._position)

    def _print_error(self) -> None:
        print(f"Error ({self._line_num}, {self._position - self._delta + 1}): unexpected character")

    def _create_token(self, domain: str, group_name: str) -> token.Token:
        assert self._match is not None
        column = self._position - self._delta + 1
        self._position = self._match.end(group_name)
        return token.Token(domain, (self._line_num, column), self._match.group(group_name))

    def next_token(self) -> token.Token:
        if self._position >= len(self._program):
            return token.Token(token.EOF_DOMAIN, (self._line_num, len(self._program) - self._delta + 1), "")

        self._match = self._find()

        if self._match is None:
            self._print_error()
            self._position += 1
            return self.next_token()

        if self._match.group(LINE_FEED_GROUP):
            self._delta = self._position = self._match.end(LINE_FEED_GROUP)
            self._line_num += 1
            return self.next_token()
        if self._match.group(VARIABLE_GROUP):
            return self._create_token(token.VAR_DOMAIN, VARIABLE_GROUP)
        if self._match.group(WORD_GROUP):
            return self._create_token(token.WORD_DOMAIN, WORD_GROUP)
        if self._match.group(NUMBER_GROUP):
            return self._create_token(token.NUMBER_DOMAIN, NUMBER_GROUP)
        if self._match.group(KEYWORD_GROUP):
            return self._create_token(self._match.group(KEYWORD_GROUP), KEYWORD_GROUP)

        self._position = self._match.end(WHITESPACES_GROUP)
        return self.next_token()
