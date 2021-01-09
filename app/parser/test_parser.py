from typing import Any, List, Union

import pytest

from .parser import AST, ParseError, parse

StrAST = List[Union[str, List[Any]]]


def to_string(ast: AST) -> StrAST:
    str_ast: StrAST = []
    for node in ast:
        if isinstance(node, list):
            str_ast.append(to_string(node))
        else:
            str_ast.append(f"{node.domain} : {node.value}")
    return str_ast


def test_new() -> None:
    assert to_string(parse("(@new (hello world))")) == [
        "@new : @new",
        ["word : hello", "word : world"]
    ]


def test_new_advanced_assertion() -> None:
    assert to_string(parse("""
    (@new
        (address
            (Pichugin Vladislav)
            (Moscow Bauman9 322)
        )
    )
    """)) == [
        "@new : @new",
        [
            "word : address",
            ["word : Pichugin", "word : Vladislav"],
            ["word : Moscow", "word : Bauman9", "number : 322"]
        ]
    ]


def test_new_rule() -> None:
    assert to_string(parse("""
    (@new
        (@rule
            (livesAbout $person1 $person2)
            (and (address $person1 ($town . $rest1))
                 (address $person2 ($town . $rest2))
                 (not (same $person1 $person2)))
        )
    )
    """)) == [
        "@new : @new",
        [
            "@rule : @rule",
            ["word : livesAbout", "var : $person1", "var : $person2"],
            [
                "and : and",
                [
                    "word : address",
                    "var : $person1",
                    ["var : $town", ". : .", "var : $rest1"]
                ],
                [
                    "word : address",
                    "var : $person2",
                    ["var : $town", ". : .", "var : $rest2"]
                ],
                [
                    "not : not",
                    ["word : same", "var : $person1", "var : $person2"]
                ]
            ]
        ]
    ]


def test_new_empty_assertion() -> None:
    assert to_string(parse("(@new ())")) == ["@new : @new", []]


def test_new_rule_with_empty_body() -> None:
    assert to_string(parse("(@new (@rule (append () $y $y)))")) == [
        "@new : @new",
        [
            "@rule : @rule",
            [
                "word : append",
                [],
                "var : $y",
                "var : $y"
            ]
        ]
    ]


def test_empty_query() -> None:
    assert to_string(parse("()")) == []


def test_simple_query() -> None:
    assert to_string(parse("(position $x (programmer $type))")) == [
        "word : position",
        "var : $x",
        [
            "word : programmer",
            "var : $type"
        ]
    ]


def test_simple_query_with_dot() -> None:
    assert to_string(parse("(position $x (programmer . $type))")) == [
        "word : position",
        "var : $x",
        [
            "word : programmer",
            ". : .",
            "var : $type"
        ]
    ]


def test_simple_query_advanced() -> None:
    assert to_string(parse("(test 999 (() $v1 666 aaa . $rest) $var)")) == [
        "word : test",
        "number : 999",
        [
            [],
            "var : $v1",
            "number : 666",
            "word : aaa",
            ". : .",
            "var : $rest"
        ],
        "var : $var"
    ]


def test_query_with_apply() -> None:
    assert to_string(parse("""
    (or
        (salary $person $amount)
        (@apply > $amount 3000)
        (@apply < $amount 10)
    )
    """)) == [
        "or : or",
        ["word : salary", "var : $person", "var : $amount"],
        ["@apply : @apply", "> : >", "var : $amount", "number : 3000"],
        ["@apply : @apply", "< : <", "var : $amount", "number : 10"],
    ]


def test_parse_error() -> None:
    with pytest.raises(ParseError):
        parse("(@new (@rule (same $x $x))")
