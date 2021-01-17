from typing import Any, Dict, List, Union

from app.interpreter.interpreter import ALL_ASSERTIONS, ALL_RULES, Interpreter
from app.parser import AST


def ast_to_string(ast_dict: Dict[str, List[AST]]) -> Dict[str, List[Union[str, List[Any]]]]:
    def to_string(tree: AST) -> List[Union[str, List[Any]]]:
        str_ast = []
        for node in tree:
            if isinstance(node, list):
                str_ast.append(to_string(node))
            else:
                str_ast.append(node.value)
        return str_ast

    res = {}
    for key, ast in ast_dict.items():
        res[key] = to_string(ast)
    return res


def run_commands(commands: List[str]) -> List[str]:
    results = []
    i = Interpreter(results.append)
    for cmd in commands:
        i.run(cmd)
    return results


def test_simple():
    assert run_commands([
        "(@new (hello world))",
        "(@new (hello (Pichugin Vladislav)))",
        "(hello $x)"
    ]) == [
               "(hello world)",
               "(hello (Pichugin Vladislav))"
           ]


def test_simple2():
    assert run_commands([
        "(@new (position (Pichugin Vladislav) (junior developer)))",
        "(@new (position (Ivan Ivanov) (senior developer)))",
        "(@new (position Jack (junior developer)))",
        "(position $name (junior developer))"
    ]) == [
               "(position (Pichugin Vladislav) (junior developer))",
               "(position Jack (junior developer))"
           ]


def test_simple3():
    assert run_commands([
        "(@new (address Vlad (Moscow 9)))",
        "(@new (address (Ivan Ivanov) Spb))",
        "(@new (nonAddress (Some Name) empty))",
        "(@new (address (Nikita Nikitin) (Nizhnevartovsk (Mira street) 123)))",
        "(address $x $y)"
    ]) == [
               "(address Vlad (Moscow 9))",
               "(address (Ivan Ivanov) Spb)",
               "(address (Nikita Nikitin) (Nizhnevartovsk (Mira street) 123))"
           ]


def test_simple_identical_vars():
    assert run_commands([
        "(@new (boss Mike Jack))",
        "(@new (boss Bob Jack))",
        "(@new (boss Jack Jack))",
        "(boss $x $x)"
    ]) == [
               "(boss Jack Jack)"
           ]


def test_simple_dot_tail():
    assert run_commands([
        "(@new (position (Pichugin Vladislav) (developer frontend backend)))",
        "(@new (position (Ivan Ivanov) (developer android)))",
        "(@new (position Ekaterina (HR)))",
        "(@new (position Nikita (developer)))",
        "(position $x (developer . $type))"
    ]) == [
               "(position (Pichugin Vladislav) (developer frontend backend))",
               "(position (Ivan Ivanov) (developer android))",
               "(position Nikita (developer))"
           ]


def test_simple_without_dot_tail():
    assert run_commands([
        "(@new (position (Pichugin Vladislav) (developer frontend backend)))",
        "(@new (position (Ivan Ivanov) (developer android)))",
        "(@new (position Ekaterina (HR)))",
        "(@new (position Nikita (developer)))",
        "(position $x (developer $type))"
    ]) == [
               "(position (Ivan Ivanov) (developer android))"
           ]


def test_compound_and():
    assert run_commands([
        "(@new (position Vlad developer))",
        "(@new (position Ekaterina HR))",
        "(@new (position Anna developer))",
        "(@new (address Vlad (Moscow (street 9) 20)))",
        "(@new (address Ekaterina (Spb 13)))",
        "(@new (address Anna (Nizhnevartovsk (Lenin street 22) 19)))",
        "(@and (position $person developer) (address $person $where))"
    ]) == [
               "(@and (position Vlad developer) (address Vlad (Moscow (street 9) 20)))",
               "(@and (position Anna developer) (address Anna (Nizhnevartovsk (Lenin street 22) 19)))"
           ]


def test_compound_or():
    assert run_commands([
        "(@new (boss Vlad Denis))",
        "(@new (boss Nikita Boris))",
        "(@new (boss Oleg Sergey))",
        "(@new (boss Alexander Boris))",
        "(@new (boss Anna Vlad))",
        "(@or (boss $x Denis) (boss $x Boris))"
    ]) == [
               "(@or (boss Vlad Denis) (boss Vlad Boris))",
               "(@or (boss Nikita Denis) (boss Nikita Boris))",
               "(@or (boss Alexander Denis) (boss Alexander Boris))",
           ]


def test_compound_not():
    assert run_commands([
        "(@new (boss Vlad Denis))",
        "(@new (position Vlad developer))",
        "(@new (position Ekaterina HR))",
        "(@new (boss Ekaterina Denis))",
        "(@new (boss Alex Denis))",
        "(@new (position Alex developer))",
        "(@new (position Nikita analyst))",
        "(@new (boss Nikita Denis))",
        "(@and (boss $person Denis) (@not (position $person developer)))"
    ]) == [
               "(@and (boss Ekaterina Denis) (@not (position Ekaterina developer)))",
               "(@and (boss Nikita Denis) (@not (position Nikita developer)))"
           ]


def test_compound_apply():
    assert run_commands([
        "(@new (salary Vlad 90))",
        "(@new (salary John 330))",
        "(@new (salary Sergey 12))",
        "(@new (salary Viktor 66))",
        "(@new (salary Ekaterina 5))",
        "(@and (salary $person $amount) (@apply > $amount 50))"
    ]) == [
               "(@and (salary Vlad 90) (@apply > 90 50))",
               "(@and (salary John 330) (@apply > 330 50))",
               "(@and (salary Viktor 66) (@apply > 66 50))"
           ]


def test_compound_apply2():
    assert run_commands([
        "(@new (salary Vlad 90))",
        "(@new (salary John 330))",
        "(@new (salary Sergey 12))",
        "(@new (salary Viktor 66))",
        "(@new (salary Ekaterina 5))",
        """
        (@and
            (salary $person $amount)
            (@or
                (@apply > $amount 70)
                (@apply < $amount 10)
            )
        )
        """
    ]) == [
               "(@and (salary Vlad 90) (@or (@apply > 90 70) (@apply < 90 10)))",
               "(@and (salary John 330) (@or (@apply > 330 70) (@apply < 330 10)))",
               "(@and (salary Ekaterina 5) (@or (@apply > 5 70) (@apply < 5 10)))"
           ]


def test_rule1():
    assert run_commands([
        """
        (@new (@rule (livesAbout $person1 $person2)
            (@and (address $person1 ($town . $rest1))
                  (address $person2 ($town . $rest2))
                  (@not (same $person1 $person2)))))
        """,
        "(@new (@rule (same $x $x)))",
        "(@new (address Vlad (Moscow (street sample) 322)))",
        "(@new (address Darya (Moscow Arbat 1337)))",
        "(@new (address Andrey (Spb (street 1) 22)))",
        "(livesAbout $x $y)"
    ]) == [
               "(livesAbout Vlad Darya)",
               "(livesAbout Darya Vlad)"
           ]


def test_rule2():
    assert run_commands([
        """
        (@new (@rule (bigBoss $person)
            (@and (boss $middleManager $person)
                  (boss $x $middleManager))))
        """,
        "(@new (position Denis developer))",
        "(@new (boss Vlad Denis))",
        "(@new (position Vlad developer))",
        "(@new (boss Alex Vlad))",
        "(@new (position Alex developer))",
        "(@new (position Nika HR))",
        "(@new (boss Alla Nika))",
        "(@new (position Alla HR))",
        "(@new (boss Ekaterina Alla))",
        "(@new (position Ekaterina HR))",
        "(@and (position $person developer) (bigBoss $person))"
    ]) == [
               "(@and (position Denis developer) (bigBoss Denis))"
           ]


def test_rule_append():
    assert run_commands([
        "(@new (@rule (append () $y $y)))",
        "(@new (@rule (append ($u . $v) $y ($u . $z)) (append $v $y $z)))",
        "(append (a b) (c d) $z)"
    ]) == [
               "(append (a b) (c d) (a b c d))"
           ]


def test_rule_append2():
    assert run_commands([
        "(@new (@rule (append () $y $y)))",
        "(@new (@rule (append ($u . $v) $y ($u . $z)) (append $v $y $z)))",
        "(append (a b) $y (a b c d))"
    ]) == [
               "(append (a b) (c d) (a b c d))"
           ]


def test_rule_append3():
    assert run_commands([
        "(@new (@rule (append () $y $y)))",
        "(@new (@rule (append ($u . $v) $y ($u . $z)) (append $v $y $z)))",
        "(append $x $y (a b c d))"
    ]) == [
               "(append () (a b c d) (a b c d))",
               "(append (a) (b c d) (a b c d))",
               "(append (a b) (c d) (a b c d))",
               "(append (a b c) (d) (a b c d))",
               "(append (a b c d) () (a b c d))"
           ]


def test_rule_next():
    assert run_commands([
        "(@new (@rule ($x nextTo $y in ($x $y . $u))))",
        "(@new (@rule ($x nextTo $y in ($v . $z)) ($x nextTo $y in $z)))",
        "($x nextTo $y in (1 (2 3) 4))"
    ]) == [
               "(1 nextTo (2 3) in (1 (2 3) 4))",
               "((2 3) nextTo 4 in (1 (2 3) 4))"
           ]


def test_rule_next2():
    assert run_commands([
        "(@new (@rule ($x nextTo $y in ($x $y . $u))))",
        "(@new (@rule ($x nextTo $y in ($v . $z)) ($x nextTo $y in $z)))",
        "($x nextTo 1 in (2 1 3 1))"
    ]) == [
               "(2 nextTo 1 in (2 1 3 1))",
               "(3 nextTo 1 in (2 1 3 1))"
           ]


def test_indexing():
    i = Interpreter(None)
    i.run("(@new (position (Pichugin Vladislav) developer))")
    i.run("(@new (@rule (selfBoss $x) (boss $x $x)))")
    i.run("(@new ((birth date) Vlad (19 April)))")
    i.run("(@new (@rule ($x nextTo $y in ($x $y . $u))))")
    i.run("(@new (position Ekaterina HR))")
    i.run("(@new (@rule ($x nextTo $y in ($v . $z)) ($x nextTo $y in $z)))")
    i.run("(@new (city Vlad Nizhnevartovsk))")
    i.run("(@new (@rule ((not index) $x) (test $x)))")
    i.run("(@new (3 follows 2))")
    assert ast_to_string(i.assertions) == {
        ALL_ASSERTIONS: [
            ["position", ["Pichugin", "Vladislav"], "developer"],
            [["birth", "date"], "Vlad", ["19", "April"]],
            ["position", "Ekaterina", "HR"],
            ["city", "Vlad", "Nizhnevartovsk"],
            ["3", "follows", "2"]
        ],
        "position": [
            ["position", ["Pichugin", "Vladislav"], "developer"],
            ["position", "Ekaterina", "HR"]
        ],
        "city": [
            ["city", "Vlad", "Nizhnevartovsk"]
        ],
        "3": [
            ["3", "follows", "2"]
        ]
    }
    assert ast_to_string(i.rules) == {
        ALL_RULES: [
            ["@rule", ["selfBoss", "$x"], ["boss", "$x", "$x"]],
            ["@rule", ["$x", "nextTo", "$y", "in", ["$x", "$y", ".", "$u"]]],
            ["@rule", ["$x", "nextTo", "$y", "in", ["$v", ".", "$z"]], ["$x", "nextTo", "$y", "in", "$z"]],
            ["@rule", [["not", "index"], "$x"], ["test", "$x"]]
        ],
        "selfBoss": [
            ["@rule", ["selfBoss", "$x"], ["boss", "$x", "$x"]]
        ],
        "$": [
            ["@rule", ["$x", "nextTo", "$y", "in", ["$x", "$y", ".", "$u"]]],
            ["@rule", ["$x", "nextTo", "$y", "in", ["$v", ".", "$z"]], ["$x", "nextTo", "$y", "in", "$z"]]
        ]
    }


def test_depends_on():
    assert run_commands([
        "(@new (@rule (testDepends $y ($z $y))))",
        "(testDepends $x $x)"
    ]) == []


def test_apply_without_binding():
    assert run_commands([
        "(@new (salary Vlad 90))",
        "(@new (salary John 330))",
        "(@new (salary Sergey 12))",
        "(@new (salary Viktor 66))",
        "(@new (salary Ekaterina 5))",
        "(@and (salary $person $amount) (@apply > $nonBind 50))"
    ]) == []


def test_apply_nested_vars():
    assert run_commands([
        "(@new (@rule (testHelper $x $y)))",
        "(@new (@rule (test $x $y) (@and (testHelper $x $y) (@apply > $x $y))))",
        "(test $x $y)"
    ]) == []


def test_get_all():
    assert run_commands([
        """
        (@new (@rule (bigBoss $person)
            (@and (boss $middleManager $person)
                  (boss $x $middleManager))))
        """,
        "(@new (position Denis developer))",
        "(@new (boss Vlad Denis))",
        "(@new (position Vlad developer))",
        "(@new (boss Alex Vlad))",
        "(@new (position Alex developer))",
        "(@new (position Nika HR))",
        "(@new (boss Alla Nika))",
        "(@new (position Alla HR))",
        "(@new (boss Ekaterina Alla))",
        "(@new (position Ekaterina HR))",
        "(. $all)"
    ]) == [
               "(position Denis developer)",
               "(boss Vlad Denis)",
               "(position Vlad developer)",
               "(boss Alex Vlad)",
               "(position Alex developer)",
               "(position Nika HR)",
               "(boss Alla Nika)",
               "(position Alla HR)",
               "(boss Ekaterina Alla)",
               "(position Ekaterina HR)",
               "(bigBoss Denis)",
               "(bigBoss Nika)"
           ]


def test_empty_select():
    assert run_commands([
        """
        (@new (@rule (bigBoss $person)
            (@and (boss $middleManager $person)
                  (boss $x $middleManager))))
        """,
        "(@new (position Denis developer))",
        "(@new (boss Vlad Denis))",
        "(@new (position Vlad developer))",
        "(@new (boss Alex Vlad))",
        "(@new (position Alex developer))",
        "(@new (position Nika HR))",
        "(@new (boss Alla Nika))",
        "(@new (position Alla HR))",
        "(@new (boss Ekaterina Alla))",
        "(@new (position Ekaterina HR))",
        "()"
    ]) == []


def test_instantiate_with_non_bind():
    assert run_commands([
        "(@new (@rule (test $y)))",
        "(test $x)"
    ]) == [
               "(test $y)"
           ]


def test_unknown_apply():
    assert run_commands([
        "(@new (salary Vlad 90))",
        "(@new (salary John 330))",
        "(@new (salary Sergey 12))",
        "(@new (salary Viktor 66))",
        "(@new (salary Ekaterina 5))",
        "(@and (salary $person $amount) (@apply newPredicate $amount 50))"
    ]) == []
