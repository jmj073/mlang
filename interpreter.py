# [AST class]==========================================================
class Node:
    pass

class LiteralNode(Node):
    def __init__(self, value):
        self.value = value

class VarNode(Node):
    def __init__(self, name):
        self.name = name

class AssignNode(Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class BinaryOpNode(Node):
    def __init__(self, op, left, right):
        self.op = op
        self.left = left
        self.right = right

class IfNode(Node):
    def __init__(self, cond, then_body, else_body=None):
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body

class FunctionNode(Node):
    def __init__(self, name, params, body):
        self.name = name
        self.params = params
        self.body = body

class FunctionCallNode(Node):
    def __init__(self, func, args):
        self.func = func
        self.args = args

class BlockNode(Node):
    def __init__(self, statements):
        self.statements = statements

# [environment]========================================================

class Environment:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def get(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env.vars[name]
            env = env.parent
        raise NameError(f"Variable '{name}' not found")

    def set(self, name, value):
        self.vars[name] = value

    
    def update(self, name, value):
        if name in self.vars:
            self.vars[name] = value
        elif self.parent:
            self.parent.update(name, value)
        else:
            raise NameError(f"Variable '{name}' not found")

# [tail call]==========================================================

class TailCall(Exception):
    def __init__(self, func, args):
        self.func = func
        self.args = args


class FunctionValue:
    def __init__(self, node, closure_env):
        self.node = node
        self.closure_env = closure_env  # 함수가 정의된 환경(클로저)

    def call(self, args, interpreter):
        # 꼬리 호출 최적화를 위해 한 번의 환경만 생성하고 재사용
        env = Environment(parent=self.closure_env)
        for param, arg in zip(self.node.params, args):
            env.set(param, arg)

        while True:
            try:
                # 함수 본문 실행; 이때 env는 재사용됨.
                return interpreter.execute(lambda v: v, self.node.body, env)
            except TailCall as tc:
                if tc.func is not self:
                    # 다른 함수에 대한 호출이면 예외를 전파
                    raise
                # 같은 함수에 대한 꼬리 호출이면, 인수 값들을 환경에 덮어씀.
                for param, arg in zip(self.node.params, tc.args):
                    env.set(param, arg)

# [interpreter]========================================================

def trampoline(thunk):
    while callable(thunk):
        thunk = thunk()
    return thunk

class Interpreter:
    def __init__(self):
        self.global_env = Environment()
        
    def exec(self, node, env=None):
        return trampoline(self.execute(lambda v: v, node, env))

    def execute(self, K, node, env=None):
        if env is None:
            env = self.global_env

        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method is None:
            raise NotImplementedError(f"No method visit_{type(node).__name__}")
        return method(K, node, env)

    def visit_LiteralNode(self, K, node, env):
        return lambda: K(node.value)

    def visit_VarNode(self, K, node, env):
        return lambda: K(env.get(node.name))

    def visit_AssignNode(self, K, node, env):
        def cont(value):
            # 이미 변수 "x"가 존재하면 상위 환경에서 업데이트하고,
            # 없으면 현재 환경에 설정
            try:
                env.update(node.name, value)
            except NameError:
                env.set(node.name, value)
            return value
        return lambda: self.execute(lambda v: K(cont(v)), node.value, env)

    def __evaluate_binary_op(self, op, left, right):
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            return left / right
        elif op == "<":
            return left < right
        elif op == ">":
            return left > right
        elif op == "==":
            return left == right
        elif op == "!=":
            return left != right
        else:
            raise ValueError(f"Unknown operator: {node.op}")

    def visit_BinaryOpNode(self, K, node, env):
        def cont1(left):
            return lambda: self.execute(lambda right: K(self.__evaluate_binary_op(node.op, left, right)), node.right, env)
        return lambda: self.execute(cont1, node.left, env)

    def visit_IfNode(self, K, node, env):
        def cont(cond):
            if cond:
                return lambda: self.execute(K, node.then_body, env)
            elif node.else_body:
                return lambda: self.execute(K, node.else_body, env)
            return None
        return lambda: self.execute(cont, node.cond, env)

    def visit_FunctionNode(self, K, node, env):
        func = FunctionValue(node, env)
        env.set(node.name, func)
        return lambda: K(func)

    def visit_FunctionCallNode(self, K, node, env):
        def after_func(func_value):
            def eval_args(args, acc):
                if not args:
                    if not isinstance(func_value, FunctionValue):
                        raise TypeError(f"{node.func} is not callable")
                    return K(func_value.call(acc, self))
                else:
                    first, *rest = args
                    c = lambda arg_value: eval_args(rest, acc + [arg_value])
                    return lambda: self.execute(c, first, env)
            return lambda: eval_args(node.args, [])
        return lambda: self.execute(after_func, node.func, env)


    def visit_BlockNode(self, K, node, env):
        def loop(stmts, res):
            if not stmts:
                return lambda: K(res)
            else:
                first, *rest = stmts
                return lambda: self.execute(lambda v: loop(rest, v), first, env)
        return lambda: loop(node.statements, None)

# [macro]==============================================================

class Macro:
    def __init__(self, from_pattern, to_template):
        self.from_pattern = from_pattern
        self.to_template = to_template

    def match(self, node):
        """패턴을 매칭하고 변수 바인딩을 반환"""
        if isinstance(self.from_pattern, type(node)):
            bindings = {}
            for attr, value in self.from_pattern.__dict__.items():
                if isinstance(value, str) and value.startswith("$"):
                    bindings[value] = getattr(node, attr)
                elif getattr(node, attr) != value:
                    return None
            return bindings
        return None

    def instantiate_template(self, template, bindings):
        """템플릿을 실제 AST로 변환"""
        if isinstance(template, str) and template.startswith("$"):
            return bindings.get(template)
        if isinstance(template, list):
            return [self.instantiate_template(item, bindings) for item in template]
        if isinstance(template, Node):
            return template.__class__(
                *[self.instantiate_template(attr, bindings) for attr in template.__dict__.values()]
            )
        return template

    def apply(self, node):
        bindings = self.match(node)
        if bindings is None:
            return node
        return self.instantiate_template(self.to_template, bindings)

class WhileMacro(Macro):
    def __init__(self):
        super().__init__(
            from_pattern=IfNode("$cond", "$body"),
            to_template=BlockNode([
                FunctionNode("loop", [], 
                    IfNode("$cond",
                        BlockNode(["$body", FunctionCallNode(VarNode("loop"), [])]),
                        None
                    )
                ),
                FunctionCallNode(VarNode("loop"), [])
            ])
        )

# [examples]===========================================================

interpreter = Interpreter()

# 변수 x = 0
interpreter.exec(AssignNode("x", LiteralNode(0)))

# while x < 5: x = x + 1
while_macro = WhileMacro()
while_loop = IfNode(
    BinaryOpNode("<", VarNode("x"), LiteralNode(5)),
    AssignNode("x", BinaryOpNode("+", VarNode("x"), LiteralNode(1)))
)
transformed_loop = while_macro.apply(while_loop)

# 실행
interpreter.exec(transformed_loop)

print(interpreter.global_env.get("x"))  # 5
