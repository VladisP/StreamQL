import copy
from itertools import chain

from ..parser import parse
from .helpers import *


# flake8: noqa: F405
class Interpreter:
    def __init__(self, consume: Consume):
        self.assertions = {ALL_ASSERTIONS: []}
        self.rules = {ALL_RULES: []}
        self.procedures = {
            token.LESS_OP: lambda args: args[0] < args[1],
            token.GREATER_OP: lambda args: args[0] > args[1]
        }
        self.consume = consume

    def run(self, command: str) -> None:
        command_ast = parse(command)
        if is_insert(command_ast):
            self._insert(get_entities(command_ast))
        else:
            for frame in self._run_query(command_ast, [{}]):
                self.consume(instantiate(command_ast, frame))

    def _insert(self, entities: AST) -> None:
        for entity in entities:
            if is_rule(entity):
                self._insert_rule(entity)
            else:
                self._insert_assertion(entity)

    def _insert_rule(self, rule: AST):
        self._store_rule_in_index(rule)
        old_rules = self.rules.get(ALL_RULES, [])
        self.rules[ALL_RULES] = old_rules + [rule]

    def _store_rule_in_index(self, rule: AST) -> None:
        pattern = get_conclusion(rule)
        if not is_indexable(pattern):
            return
        key = get_index_key(pattern)
        old_rules = self.rules.get(key, [])
        self.rules[key] = old_rules + [rule]

    def _insert_assertion(self, assertion: AST) -> None:
        self._store_assertion_in_index(assertion)
        old_assertions = self.assertions.get(ALL_ASSERTIONS, [])
        self.assertions[ALL_ASSERTIONS] = old_assertions + [assertion]

    def _store_assertion_in_index(self, assertion: AST) -> None:
        if not is_indexable(assertion):
            return
        key = get_index_key(assertion)
        old_assertions = self.assertions.get(key, [])
        self.assertions[key] = old_assertions + [assertion]

    def _run_query(self, query: AST, frames: List[Frame]) -> List[Frame]:
        if is_non_empty_list(query):
            if is_atom(query[0]) and query[0].domain == token.AND_KEYWORD:
                return self._and(query[1:], frames)
            if is_atom(query[0]) and query[0].domain == token.OR_KEYWORD:
                return self._or(query[1:], frames)
            if is_atom(query[0]) and query[0].domain == token.NOT_KEYWORD:
                return self._not(query[1], frames)
            if is_atom(query[0]) and query[0].domain == token.APPLY_KEYWORD:
                return self._apply(query[1].value, query[2:], frames)
        return self._run_simple_query(query, frames)

    def _and(self, conjuncts: AST, frames: List[Frame]) -> List[Frame]:
        if len(conjuncts) == 0:
            return frames
        return self._and(conjuncts[1:], self._run_query(conjuncts[0], frames))

    def _or(self, disjuncts: AST, frames: List[Frame]) -> List[Frame]:
        if len(disjuncts) == 0:
            return []
        return list(chain(*[
            self._run_query(disjuncts[0], copy.deepcopy(frames)),
            self._or(disjuncts[1:], frames)
        ]))

    def _not(self, operand: AST, frames: List[Frame]) -> List[Frame]:
        return list(chain(*[
            [frame] if len(self._run_query(operand, [frame])) == 0 else []
            for frame in frames
        ]))

    def _apply(self, predicate: str, arguments: List[AstAtom], frames: List[Frame]) -> List[Frame]:
        def execute(inst_args: Optional[List[Union[str, int]]]) -> bool:
            if inst_args is None:
                return False
            return self.procedures.get(predicate, lambda _: False)(inst_args)

        return list(chain(*[
            [frame] if execute(instantiate_args(arguments, frame)) else []
            for frame in frames
        ]))

    def _run_simple_query(self, query: AST, frames: List[Frame]) -> List[Frame]:
        return list(chain(
            *[self._find_assertions(query, frame) for frame in frames],
            *[self._apply_rules(query, frame) for frame in frames]
        ))

    def _find_assertions(self, query: AST, frame: Frame) -> List[Frame]:
        return list(chain(*[
            self._check_assertion(assertion, query, frame.copy()) for assertion in self._fetch_assertions(query)
        ]))

    def _fetch_assertions(self, pattern: AST) -> List[AST]:
        return self.assertions.get(get_index_key(pattern), []) \
            if use_index(pattern) \
            else self.assertions.get(ALL_ASSERTIONS, [])

    def _check_assertion(self, assertion: AST, query: AST, frame: Frame) -> List[Frame]:
        match_result = self._pattern_match(query, assertion, frame)
        if match_result is None:
            return []
        return [match_result]

    def _pattern_match(self, pattern: AstNode, data: AstNode, frame: Optional[Frame]) -> Optional[Frame]:
        if frame is None:
            return None
        if pattern == data:
            return frame
        if is_var(pattern):
            return self._extend_frame(pattern.value, data, frame)
        if is_non_empty_list(pattern) and is_list(data) and is_dot(pattern[0]):
            return self._pattern_match(pattern[1], data[0:], frame)
        if is_non_empty_list(pattern) and is_non_empty_list(data):
            return self._pattern_match(
                pattern[1:],
                data[1:],
                self._pattern_match(pattern[0], data[0], frame)
            )
        return None

    def _extend_frame(self, var: str, data: AST, frame: Frame) -> Optional[Frame]:
        binding = frame.get(var)
        if binding is None:
            frame[var] = data
            return frame
        return self._pattern_match(binding, data, frame)

    def _apply_rules(self, pattern: AST, frame: Frame) -> List[Frame]:
        return list(chain(*[
            self._apply_rule(rule, pattern, frame.copy()) for rule in self._fetch_rules(pattern)
        ]))

    def _fetch_rules(self, pattern: AST) -> List[AST]:
        return self.rules.get(get_index_key(pattern), []) + self.rules.get(VAR_INDEX_KEY, []) \
            if use_index(pattern) \
            else self.rules.get(ALL_RULES, [])

    def _apply_rule(self, rule: AST, query: AST, frame: Frame) -> List[Frame]:
        clean_rule = rename_variables(rule)
        unify_result = self._unify_match(query, get_conclusion(clean_rule), frame)
        if unify_result is None:
            return []
        body = get_body(clean_rule)
        if body is None:
            return [unify_result]
        return self._run_query(body, [unify_result])

    def _unify_match(self, pattern1: AstNode, pattern2: AstNode, frame: Frame) -> Optional[Frame]:
        if frame is None:
            return None
        if pattern1 == pattern2:
            return frame
        if is_var(pattern1):
            return self._unify_extend(pattern1.value, pattern2, frame)
        if is_var(pattern2):
            return self._unify_extend(pattern2.value, pattern1, frame)
        if is_non_empty_list(pattern1) and is_list(pattern2) and is_dot(pattern1[0]):
            return self._unify_match(pattern1[1], pattern2[0:], frame)
        if is_non_empty_list(pattern2) and is_list(pattern1) and is_dot(pattern2[0]):
            return self._unify_match(pattern1[0:], pattern2[1], frame)
        if is_non_empty_list(pattern1) and is_non_empty_list(pattern2):
            return self._unify_match(
                pattern1[1:],
                pattern2[1:],
                self._unify_match(pattern1[0], pattern2[0], frame)
            )
        return None

    def _unify_extend(self, var: str, data: AstNode, frame: Frame) -> Optional[Frame]:
        binding = frame.get(var)
        if binding is not None:
            return self._unify_match(binding, data, frame)
        if is_var(data):
            binding = frame.get(data.value)
            if binding is not None:
                return self._unify_match(AstAtom(token.VAR_DOMAIN, var), binding, frame)
            frame[var] = data
            return frame
        if depends_on(data, var, frame):
            return None
        frame[var] = data
        return frame
