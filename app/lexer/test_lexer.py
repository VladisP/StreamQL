from typing import List

from . import token
from .lexer import Lexer


def get_tokens_list(program: str) -> List[str]:
    lexer = Lexer(program)
    tokens = list()
    while True:
        tok = lexer.next_token()
        tokens.append(str(tok))
        if tok.domain == token.EOF_DOMAIN:
            return tokens


# flake8: noqa: W291 (trailing whitespace is needed to test the lexer)
def test_new() -> None:
    assert get_tokens_list("(@new (hello world))") == [
        "( (1, 1): (",
        "@new (1, 2): @new",
        "( (1, 7): (",
        "word (1, 8): hello",
        "word (1, 14): world",
        ") (1, 19): )",
        ") (1, 20): )",
        "eof (1, 21): "
    ]


def test_rule() -> None:
    assert get_tokens_list("""
        (@rule (livesAbout $person1 $person2)
            (and (address $person1 ($town . $rest1))
                 (address $person2 ($town . $rest2))
                 (not (same $person1 $person2))))
        """) == [
        "( (2, 9): (",
        "@rule (2, 10): @rule",
        "( (2, 16): (",
        "word (2, 17): livesAbout",
        "var (2, 28): $person1",
        "var (2, 37): $person2",
        ") (2, 45): )",
        "( (3, 13): (",
        "and (3, 14): and",
        "( (3, 18): (",
        "word (3, 19): address",
        "var (3, 27): $person1",
        "( (3, 36): (",
        "var (3, 37): $town",
        ". (3, 43): .",
        "var (3, 45): $rest1",
        ") (3, 51): )",
        ") (3, 52): )",
        "( (4, 18): (",
        "word (4, 19): address",
        "var (4, 27): $person2",
        "( (4, 36): (",
        "var (4, 37): $town",
        ". (4, 43): .",
        "var (4, 45): $rest2",
        ") (4, 51): )",
        ") (4, 52): )",
        "( (5, 18): (",
        "not (5, 19): not",
        "( (5, 23): (",
        "word (5, 24): same",
        "var (5, 29): $person1",
        "var (5, 38): $person2",
        ") (5, 46): )",
        ") (5, 47): )",
        ") (5, 48): )",
        ") (5, 49): )",
        "eof (6, 9): "
    ]


def test_apply() -> None:
    assert get_tokens_list("""
        (or 
            (salary $person $amount) 
            (@apply > $amount 3000) 
            (@apply < $amount 10)
        )
        """) == [
        "( (2, 9): (",
        "or (2, 10): or",
        "( (3, 13): (",
        "word (3, 14): salary",
        "var (3, 21): $person",
        "var (3, 29): $amount",
        ") (3, 36): )",
        "( (4, 13): (",
        "@apply (4, 14): @apply",
        "> (4, 21): >",
        "var (4, 23): $amount",
        "number (4, 31): 3000",
        ") (4, 35): )",
        "( (5, 13): (",
        "@apply (5, 14): @apply",
        "< (5, 21): <",
        "var (5, 23): $amount",
        "number (5, 31): 10",
        ") (5, 33): )",
        ") (6, 9): )",
        "eof (7, 9): "
    ]


def test_unexpected_character() -> None:
    assert get_tokens_list("(search pattern-1)") == [
        "( (1, 1): (",
        "word (1, 2): search",
        "word (1, 9): pattern",
        "number (1, 17): 1",
        ") (1, 18): )",
        "eof (1, 19): "
    ]
