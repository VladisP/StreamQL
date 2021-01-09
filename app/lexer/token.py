from dataclasses import dataclass
from typing import Tuple

LEFT_PAREN = "("
RIGHT_PAREN = ")"
NEW_KEYWORD = "@new"
RULE_KEYWORD = "@rule"
APPLY_KEYWORD = "@apply"
AND_KEYWORD = "and"
OR_KEYWORD = "or"
NOT_KEYWORD = "not"
LESS_OP = "<"
GREATER_OP = ">"
DOT = "."
VAR_DOMAIN = "var"
WORD_DOMAIN = "word"
NUMBER_DOMAIN = "number"
EOF_DOMAIN = "eof"


@dataclass(frozen=True)
class Token:
    domain: str
    coords: Tuple[int, int]
    value: str

    def __str__(self) -> str:
        row, column = self.coords
        return f"{self.domain} ({row}, {column}): {self.value}"
