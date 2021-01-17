import uuid
from typing import Callable, Dict, List, Optional, Union

from ..lexer import token
from ..parser import AST, AstAtom, AstNode

Frame = Dict[str, AstNode]
Consume = Callable[[str], None]

ALL_ASSERTIONS = "all_assertions"
ALL_RULES = "all_rules"
VAR_INDEX_KEY = "$"
ID_DELIMITER = "__"


def is_list(node: AstNode) -> bool:
    return isinstance(node, list)


def is_non_empty_list(node: AstNode) -> bool:
    return is_list(node) and len(node) > 0


def is_atom(node: AstNode) -> bool:
    return isinstance(node, AstAtom)


def is_var(node: AstNode) -> bool:
    return is_atom(node) and node.domain == token.VAR_DOMAIN


def is_constant_symbol(node: AstNode) -> bool:
    return is_atom(node) and (node.domain == token.WORD_DOMAIN or node.domain == token.NUMBER_DOMAIN)


def is_dot(node: AstNode) -> bool:
    return is_atom(node) and node.domain == token.DOT


def is_insert(ast: AST) -> bool:
    return is_non_empty_list(ast) and is_atom(ast[0]) and ast[0].domain == token.NEW_KEYWORD


def get_entities(insert_command: AST) -> AST:
    return insert_command[1:]


def is_rule(entity: AST) -> bool:
    return is_non_empty_list(entity) and is_atom(entity[0]) and entity[0].domain == token.RULE_KEYWORD


def get_conclusion(rule: AST) -> AST:
    return rule[1]


def get_body(rule: AST) -> Optional[AST]:
    if len(rule) < 3:
        return None
    return rule[2]


def is_indexable(pattern: AST) -> bool:
    return len(pattern) > 0 and (is_constant_symbol(pattern[0]) or is_var(pattern[0]))


def use_index(pattern: AST) -> bool:
    return len(pattern) > 0 and is_constant_symbol(pattern[0])


def get_index_key(pattern: AST) -> str:
    atom = pattern[0]
    return VAR_INDEX_KEY if is_var(atom) else atom.value


def rename_variables(rule: AST) -> AST:
    var_id = uuid.uuid4().__str__()

    def tree_walk(exp: AstNode) -> AstNode:
        if is_var(exp):
            return make_id_variable(exp.value, var_id)
        if is_non_empty_list(exp):
            return [tree_walk(exp[0])] + tree_walk(exp[1:])
        return exp

    return tree_walk(rule)


def make_id_variable(var: str, var_id: str) -> AstAtom:
    return AstAtom(token.VAR_DOMAIN, f"{var}{ID_DELIMITER}{var_id}")


def depends_on(expression: AstNode, var: str, frame: Frame) -> bool:
    def tree_walk(exp: AstNode) -> bool:
        if is_var(exp):
            if exp.value == var:
                return True
            binding = frame.get(exp.value)
            if binding is not None:
                return tree_walk(binding)
            return False
        if is_non_empty_list(exp):
            return tree_walk(exp[0]) or tree_walk(exp[1:])
        return False

    return tree_walk(expression)


def instantiate(pattern: AST, frame: Frame) -> str:
    def helper(node: AstNode) -> AstNode:
        if is_var(node):
            binding = frame.get(node.value)
            return helper(binding) \
                if binding is not None \
                else AstAtom(domain=token.VAR_DOMAIN, value=node.value.split(ID_DELIMITER)[0])
        if is_non_empty_list(node) and is_dot(node[0]):
            return helper(node[1])
        if is_non_empty_list(node):
            return [helper(node[0])] + helper(node[1:])
        return node

    return ast_to_string(helper(pattern))


def ast_to_string(ast: AST) -> str:
    res = ""
    for node in ast:
        res += f"{ast_to_string(node)} " if is_list(node) else f"{node.value} "
    return f"({res.strip()})"


def instantiate_args(args: List[AstAtom], frame: Frame) -> Optional[List[Union[str, int]]]:
    def instantiate_var(var: str) -> Optional[Union[str, int]]:
        binding = frame.get(var)
        if binding is None or is_list(binding):
            return None
        if is_var(binding):
            return instantiate_var(binding.value)
        return int(binding.value) if binding.value.isnumeric() else binding.value

    res = []
    for atom in args:
        if is_var(atom):
            inst = instantiate_var(atom.value)
            if inst is None:
                return None
            res.append(inst)
        else:
            res.append(int(atom.value) if atom.value.isnumeric() else atom.value)
    return res
