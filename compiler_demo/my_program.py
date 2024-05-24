import os

from . import my_parser
from . import my_semantic


def execute(prog: str) -> None:
    prog = my_parser.parse(prog)

    print('ast:')
    print(*prog.tree, sep=os.linesep)
    print()

    print('semantic_check:')
    try:
        scope = my_semantic.prepare_global_scope()
        prog.semantic_check(scope)
        print(*prog.tree, sep=os.linesep)
    except my_semantic.SemanticException as e:
        print('Ошибка: {}'.format(e.message))
        return
    print()
