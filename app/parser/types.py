from dataclasses import dataclass
from typing import Any, List, Union

from app.lexer import token


@dataclass(frozen=True)
class AstAtom:
    domain: str
    value: str

    def __str__(self) -> str:
        return f"{self.domain} : {self.value}"


def token_to_atom(tok: token.Token) -> AstAtom:
    return AstAtom(tok.domain, tok.value)


AST = List[Union[AstAtom, List[Any]]]
AstNode = Union[AstAtom, AST]


class ParseError(Exception):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self) -> str:
        return self.message
