from typing import List

from app.lexer import Lexer, token

from .types import AST, ParseError, token_to_atom


def parse(program: str) -> AST:
    return Parser(Lexer(program)).parse_command()


class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.current = lexer.next_token()

    def _expect(self, expected: List[str]) -> None:
        if self.current.domain not in expected:
            row, column = self.current.coords
            raise ParseError(f"({row}, {column}): expected '{', '.join(expected)}', got '{self.current.value}'")

    def _next(self) -> None:
        self.current = self.lexer.next_token()

    # Command ::= '(' Insert | Query ')'
    def parse_command(self) -> AST:
        self._expect([token.LEFT_PAREN])
        self._next()
        ast = self._parse_insert() if self.current.domain == token.NEW_KEYWORD else self._parse_query()
        self._expect([token.RIGHT_PAREN])
        self._next()
        self._expect([token.EOF_DOMAIN])
        return ast

    # Insert ::= '@new' Entity
    def _parse_insert(self) -> AST:
        self._expect([token.NEW_KEYWORD])
        ast: AST = [token_to_atom(self.current)]
        self._next()
        ast.append(self._parse_entity())
        return ast

    # Entity ::= '(' Assertion | Rule ')'
    def _parse_entity(self) -> AST:
        self._expect([token.LEFT_PAREN])
        self._next()
        ast = self._parse_rule() if self.current.domain == token.RULE_KEYWORD else self._parse_assertion()
        self._expect([token.RIGHT_PAREN])
        self._next()
        return ast

    # Assertion ::= ('(' Assertion ')' | Word | Number)*
    def _parse_assertion(self) -> AST:
        expected_domains = [token.LEFT_PAREN, token.WORD_DOMAIN, token.NUMBER_DOMAIN]
        ast: AST = []
        while self.current.domain in expected_domains:
            if self.current.domain == token.LEFT_PAREN:
                self._next()
                ast.append(self._parse_assertion())
                self._expect([token.RIGHT_PAREN])
            else:
                ast.append(token_to_atom(self.current))
            self._next()
        return ast

    # Rule ::= '@rule' '(' SimpleQuery ')' ('(' Query ')')?
    def _parse_rule(self) -> AST:
        self._expect([token.RULE_KEYWORD])
        ast: AST = [token_to_atom(self.current)]
        self._next()
        self._expect([token.LEFT_PAREN])
        self._next()
        ast.append(self._parse_simple_query())
        self._expect([token.RIGHT_PAREN])
        self._next()
        if self.current.domain == token.LEFT_PAREN:
            self._next()
            ast.append(self._parse_query())
            self._expect([token.RIGHT_PAREN])
            self._next()
        return ast

    # Query ::= SimpleQuery | AndQuery | OrQuery | NotQuery
    def _parse_query(self) -> AST:
        if self.current.domain == token.AND_KEYWORD:
            return self._parse_and_query()
        if self.current.domain == token.OR_KEYWORD:
            return self._parse_or_query()
        if self.current.domain == token.NOT_KEYWORD:
            return self._not_query()
        return self._parse_simple_query()

    # AndQuery ::= '@and' InnerQueries
    def _parse_and_query(self) -> AST:
        self._expect([token.AND_KEYWORD])
        ast: AST = [token_to_atom(self.current)]
        self._next()
        return [*ast, *self._parse_inner_queries()]

    # OrQuery ::= '@or' InnerQueries
    def _parse_or_query(self) -> AST:
        self._expect([token.OR_KEYWORD])
        ast = [token_to_atom(self.current)]
        self._next()
        return [*ast, *self._parse_inner_queries()]

    # NotQuery ::= '@not' InnerQuery
    def _not_query(self) -> AST:
        self._expect([token.NOT_KEYWORD])
        ast: AST = [token_to_atom(self.current)]
        self._next()
        ast.append(self._parse_inner_query())
        return ast

    # InnerQueries ::= InnerQuery+
    def _parse_inner_queries(self) -> AST:
        self._expect([token.LEFT_PAREN])
        ast: AST = []
        while self.current.domain == token.LEFT_PAREN:
            ast.append(self._parse_inner_query())
        return ast

    # InnerQuery ::= '(' Query | Apply ')'
    def _parse_inner_query(self) -> AST:
        self._expect([token.LEFT_PAREN])
        self._next()
        ast = self._parse_apply() if self.current.domain == token.APPLY_KEYWORD else self._parse_query()
        self._expect([token.RIGHT_PAREN])
        self._next()
        return ast

    # Apply ::= '@apply' Predicate ApplyArguments
    # Predicate ::= '<' | '>' | Word
    # ApplyArguments ::= (Var | Word | Number)+
    def _parse_apply(self) -> AST:
        self._expect([token.APPLY_KEYWORD])
        ast: AST = [token_to_atom(self.current)]
        self._next()
        self._expect([token.LESS_OP, token.GREATER_OP, token.WORD_DOMAIN])
        ast.append(token_to_atom(self.current))
        self._next()
        expected_domains = [token.VAR_DOMAIN, token.WORD_DOMAIN, token.NUMBER_DOMAIN]
        self._expect(expected_domains)
        while self.current.domain in expected_domains:
            ast.append(token_to_atom(self.current))
            self._next()
        return ast

    # SimpleQuery ::= ('(' SimpleQuery ')' | Var | Word | Number)* ('.' Var)?
    def _parse_simple_query(self) -> AST:
        expected_domains = [token.LEFT_PAREN, token.VAR_DOMAIN, token.WORD_DOMAIN, token.NUMBER_DOMAIN]
        ast: AST = []
        while self.current.domain in expected_domains:
            if self.current.domain == token.LEFT_PAREN:
                self._next()
                ast.append(self._parse_simple_query())
                self._expect([token.RIGHT_PAREN])
            else:
                ast.append(token_to_atom(self.current))
            self._next()
        if self.current.domain == token.DOT:
            ast.append(token_to_atom(self.current))
            self._next()
            self._expect([token.VAR_DOMAIN])
            ast.append(token_to_atom(self.current))
            self._next()
        return ast
