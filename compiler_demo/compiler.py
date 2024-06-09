from compiler_demo.ast_nodes import *
from compiler_demo.my_parser import parse


class Compiler:
    def __init__(self, ast):
        self.ast = ast

    def compile(self):
        compiled_code = self._compile_node(self.ast)
        return compiled_code

    def _compile_node(self, node):
        if isinstance(node, StmtListNode):
            return '\n'.join(self._compile_node(stmt) for stmt in node.childs)
        elif isinstance(node, AssignNode):
            return f'{node.name} = {self._compile_node(node.val)}'
        elif isinstance(node, BinOpNode):
            return f'({self._compile_node(node.arg1)} {node.op.value} {self._compile_node(node.arg2)})'

        elif isinstance(node, CallNode):
            args = ', '.join(self._compile_node(arg) for arg in node.args)
            if node.name == "вывод":
                return f'print({args})'
            return f'{node.name}({args})'
        elif isinstance(node, FuncNode):
            params = ', '.join(f'{param.name}' for param in node.params if param is not None)
            body = self._compile_node(node.body).replace('\n', '\n    ')  # Отступ для тела функции
            return f'def {node.name}({params}):\n    {body}'
        elif isinstance(node, LiteralNode):
            return str(node.value)
        elif isinstance(node, IdentNode):
            return node.name
        elif isinstance(node, IfNode):
            then_part = self._compile_node(node.then).replace('\n', '\n    ')  # Отступ для блока then
            else_part = self._compile_node(node.else_).replace('\n', '\n    ')  # Отступ для блока else
            return f'if {self._compile_node(node.cond)}:\n    {then_part}\nelse:\n    {else_part}'
        elif isinstance(node, ForNode):
            init = self._compile_node(node.init)
            cond = self._compile_node(node.cond)
            incr = self._compile_node(node.incr)
            body = self._compile_node(node.body).replace('\n', '\n    ')  # Отступ для тела цикла
            return f'for {init}; {cond}; {incr}:\n    {body}'
        elif isinstance(node, WhileNode):
            body = self._compile_node(node.body).replace('\n', '\n    ')  # Отступ для тела цикла
            return f'while {self._compile_node(node.cond)}:\n    {body}'

    def execute(self, compiled_code):
        exec_globals = {}
        exec(compiled_code, exec_globals)
        return exec_globals


# Пример использования компилятора
program = '''
        цел ввод_цел(лит имя)
        нач
            если имя != "" то нач
                вывод("Введите " + имя + ": ");
            кон
            вернуть в_цел(read());
        кон
        вещ input_вещ(лит имя)
        нач
            если имя != "" то нач
                вывод("Введите " + имя + ": ");
            кон
            вернуть в_вещ(read());
        кон

        цел g, g2 = g, g4 = 90;

        цел a = ввод_цел("a");
        вещ b = input_вещ("b"), c = input_вещ("c");  /* comment 1
        цел d = ввод_цел("d");
        */
        для (цел i = 0, j = 8; ((i <= 5)) && g; i = i + 1, вывод(5))
            для(; a < b;)
                если a > 7 + b то
                нач
                    c = a + b * (2 - 1) + 0;  // comment 2
                    лит bb = "98\tура";
                кон
                иначе
                    если a то
                        вывод((c + 1) + " " + 89.89);
        для(лог i = true;;);

        цел z;
        z= 0;
    '''

# Парсинг программы
parsed_ast = parse(program)

# Компиляция в Python
compiler = Compiler(parsed_ast)
compiled_code = compiler.compile()

print("Скомпилированный Python код:\n")
print(compiled_code)

# Выполнение скомпилированного кода
exec_globals = compiler.execute(compiled_code)
print(exec_globals)
