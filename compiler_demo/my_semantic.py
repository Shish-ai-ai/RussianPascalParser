from typing import Tuple, Any, Dict, Optional
from enum import Enum

class BinOp(Enum):
    """Перечисление возможных биранных операций
    """

    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MOD = '%'
    GT = '>'
    LT = '<'
    GE = '>='
    LE = '<='
    EQUALS = '=='
    NEQUALS = '!='
    BIT_AND = '&'
    BIT_OR = '|'
    LOGICAL_AND = '&&'
    LOGICAL_OR = '||'

    def __str__(self):
        return self.value


class BaseType(Enum):
    """Перечисление для базовых типов данных
    """

    VOID = 'пусто'
    INT = 'цел'
    FLOAT = 'вещ'
    BOOL = 'лог'
    STR = 'лит'

    def __str__(self):
        return self.value


VOID, INT, FLOAT, BOOL, STR = BaseType.VOID, BaseType.INT, BaseType.FLOAT, BaseType.BOOL, BaseType.STR


class TypeDesc:
    """Класс для описания типа данных.

       Сейчас поддерживаются только примитивные типы данных и функции.
       При поддержки сложных типов (массивы и т.п.) должен быть рассширен
    """

    VOID: 'TypeDesc'
    INT: 'TypeDesc'
    FLOAT: 'TypeDesc'
    BOOL: 'TypeDesc'
    STR: 'TypeDesc'

    def __init__(self, base_type_: Optional[BaseType] = None,
                 return_type: Optional['TypeDesc'] = None, params: Optional[Tuple['TypeDesc']] = None,
                 is_array: bool = False, dimensions: int = 1) -> None:
        self.base_type = base_type_
        self.return_type = return_type
        self.params = params
        self.is_array = is_array
        self.dimensions = dimensions

    @property
    def func(self) -> bool:
        return self.return_type is not None

    @property
    def is_simple(self) -> bool:
        return not self.func and not self.is_array

    def __eq__(self, other: 'TypeDesc'):
        if self.func != other.func or self.is_array != other.is_array:
            return False
        if not self.func and not self.is_array:
            return self.base_type == other.base_type
        elif self.is_array:
            return self.base_type == other.base_type and self.dimensions == other.dimensions
        else:
            if self.return_type != other.return_type:
                return False
            if len(self.params) != len(other.params):
                return False
            for i in range(len(self.params)):
                if self.params[i] != other.params[i]:
                    return False
            return True

    @staticmethod
    def from_base_type(base_type_: BaseType) -> 'TypeDesc':
        return getattr(TypeDesc, base_type_.name)

    @staticmethod
    def from_str(str_decl: str) -> 'TypeDesc':
        try:
            base_type_ = BaseType(str_decl)
            return TypeDesc.from_base_type(base_type_)
        except:
            raise SemanticException('Неизвестный тип {}'.format(str_decl))

    def __str__(self) -> str:
        if self.is_array:
            return f'{self.base_type}[]'
        elif not self.func:
            return str(self.base_type)
        else:
            res = str(self.return_type)
            res += ' ('
            for param in self.params:
                if res[-1] != '(':
                    res += ', '
                res += str(param)
            res += ')'
        return res


for base_type in BaseType:
    setattr(TypeDesc, base_type.name, TypeDesc(base_type))


class ScopeType(Enum):
    """Перечисление для "области" декларации переменных
    """

    GLOBAL = 'global'
    GLOBAL_LOCAL = 'global.local'  # переменные относятся к глобальной области, но описаны в скобках (теряем имена)
    PARAM = 'param'
    LOCAL = 'local'

    def __str__(self):
        return self.value


class IdentDesc:
    """Класс для описания переменых
    """

    def __init__(self, name: str, type_: TypeDesc, scope: ScopeType = ScopeType.GLOBAL, index: int = 0) -> None:
        self.name = name
        self.type = type_
        self.scope = scope
        self.index = index
        self.built_in = False

    def __str__(self) -> str:
        return '{}, {}, {}'.format(self.type, self.scope, 'built-in' if self.built_in else self.index)


class IdentScope:
    """Класс для представлений областей видимости переменных во время семантического анализа
    """

    def __init__(self, parent: Optional['IdentScope'] = None) -> None:
        self.idents: Dict[str, IdentDesc] = {}
        self.func: Optional[IdentDesc] = None
        self.parent = parent
        self.var_index = 0
        self.param_index = 0

    @property
    def is_global(self) -> bool:
        return self.parent is None

    @property
    def curr_global(self) -> 'IdentScope':
        curr = self
        while curr.parent:
            curr = curr.parent
        return curr

    @property
    def curr_func(self) -> Optional['IdentScope']:
        curr = self
        while curr and not curr.func:
            curr = curr.parent
        return curr

    def add_ident(self, ident: IdentDesc) -> IdentDesc:
        func_scope = self.curr_func
        global_scope = self.curr_global

        if ident.scope != ScopeType.PARAM:
            ident.scope = ScopeType.LOCAL if func_scope else \
                ScopeType.GLOBAL if self == global_scope else ScopeType.GLOBAL_LOCAL

        old_ident = self.get_ident(ident.name)
        if old_ident:
            error = False
            if ident.scope == ScopeType.PARAM:
                if old_ident.scope == ScopeType.PARAM:
                    error = True
            elif ident.scope == ScopeType.LOCAL:
                if old_ident.scope not in (ScopeType.GLOBAL, ScopeType.GLOBAL_LOCAL):
                    error = True
            else:
                error = True
            if error:
                raise SemanticException('Идентификатор {} уже объявлен'.format(ident.name))

        if not ident.type.func and not ident.type.is_array:
            if ident.scope == ScopeType.PARAM:
                ident.index = func_scope.param_index
                func_scope.param_index += 1
            else:
                ident_scope = func_scope if func_scope else global_scope
                ident.index = ident_scope.var_index
                ident_scope.var_index += 1

        self.idents[ident.name] = ident
        return ident

    def get_ident(self, name: str) -> Optional[IdentDesc]:
        scope = self
        ident = None
        while scope:
            ident = scope.idents.get(name)
            if ident:
                break
            scope = scope.parent
        return ident


class SemanticException(Exception):
    """Класс для исключений во время семантического анализаё
    """

    def __init__(self, message, row: int = None, col: int = None, **kwargs: Any) -> None:
        if row or col:
            message += " ("
            if row:
                message += 'строка: {}'.format(row)
                if col:
                    message += ', '
            if row:
                message += 'позиция: {}'.format(col)
            message += ")"
        self.message = message


TYPE_CONVERTIBILITY = {
    INT: (FLOAT, BOOL, STR),
    FLOAT: (STR,),
    BOOL: (STR,)
}


def can_type_convert_to(from_type: TypeDesc, to_type: TypeDesc) -> bool:
    if not from_type.is_simple or not to_type.is_simple:
        return False
    return from_type.base_type in TYPE_CONVERTIBILITY and to_type.base_type in TYPE_CONVERTIBILITY[to_type.base_type]


BIN_OP_TYPE_COMPATIBILITY = {
    BinOp.ADD: {
        (INT, INT): INT,
        (FLOAT, FLOAT): FLOAT,
        (STR, STR): STR
    },
    BinOp.SUB: {
        (INT, INT): INT,
        (FLOAT, FLOAT): FLOAT
    },
    BinOp.MUL: {
        (INT, INT): INT,
        (FLOAT, FLOAT): FLOAT
    },
    BinOp.DIV: {
        (INT, INT): INT,
        (FLOAT, FLOAT): FLOAT
    },
    BinOp.MOD: {
        (INT, INT): INT,
        (FLOAT, FLOAT): FLOAT
    },

    BinOp.GT: {
        (INT, INT): BOOL,
        (FLOAT, FLOAT): BOOL,
        (STR, STR): BOOL,
    },
    BinOp.LT: {
        (INT, INT): BOOL,
        (FLOAT, FLOAT): BOOL,
        (STR, STR): BOOL,
    },
    BinOp.GE: {
        (INT, INT): BOOL,
        (FLOAT, FLOAT): BOOL,
        (STR, STR): BOOL,
    },
    BinOp.LE: {
        (INT, INT): BOOL,
        (FLOAT, FLOAT): BOOL,
        (STR, STR): BOOL,
    },
    BinOp.EQUALS: {
        (INT, INT): BOOL,
        (FLOAT, FLOAT): BOOL,
        (STR, STR): BOOL,
    },
    BinOp.NEQUALS: {
        (INT, INT): BOOL,
        (FLOAT, FLOAT): BOOL,
        (STR, STR): BOOL,
    },

    BinOp.BIT_AND: {
        (INT, INT): INT
    },
    BinOp.BIT_OR: {
        (INT, INT): INT
    },

    BinOp.LOGICAL_AND: {
        (BOOL, BOOL): BOOL
    },
    BinOp.LOGICAL_OR: {
        (BOOL, BOOL): BOOL
    },
}


BUILT_IN_OBJECTS = '''
    лит read() нач кон
    пусто вывод (лит p0) нач кон
    пусто вывод_цел(лит p0) нач кон
    цел в_цел(лит p0) нач кон
    цел в_вещ(лит p0) нач кон
'''


def prepare_global_scope() -> IdentScope:
    from compiler_demo.my_parser import parse

    prog = parse(BUILT_IN_OBJECTS)
    scope = IdentScope()
    prog.semantic_check(scope)
    for name, ident in scope.idents.items():
        ident.built_in = True
    scope.var_index = 0
    return scope
