class BaseNode:
    def __init__(self, type):
        self.type = type

    def match(self, other):
        """패턴과 매칭된 값을 딕셔너리로 반환"""
        if not isinstance(other, BaseNode) or self.type != other.type:
            return None
        return {}  # 빈 딕셔너리라도 반환해야 계속 매칭 가능


class IfNode(BaseNode):
    def __init__(self, condition=None, body=None, else_body=None):
        super().__init__("if")
        self.condition = condition
        self.body = body or []
        self.else_body = else_body or []

    def match(self, other):
        if super().match(other) is None:
            return None

        match_result = {}
        matched_cond = match_pattern(self.condition, other.condition)
        matched_body = match_list_pattern(self.body, other.body)
        matched_else = match_list_pattern(self.else_body, other.else_body)

        if matched_cond is None or matched_body is None or matched_else is None:
            return None

        match_result.update(matched_cond)
        match_result.update(matched_body)
        match_result.update(matched_else)
        return match_result


class BinaryOpNode(BaseNode):
    def __init__(self, left, op, right):
        super().__init__("binary_op")
        self.left = left
        self.op = op
        self.right = right

    def match(self, other):
        if super().match(other) is None:
            return None

        if self.op != other.op:
            return None  # 연산자가 다르면 매칭 실패

        match_result = {}
        matched_left = match_pattern(self.left, other.left)
        matched_right = match_pattern(self.right, other.right)

        if matched_left is None or matched_right is None:
            return None

        match_result.update(matched_left)
        match_result.update(matched_right)
        return match_result


class ForNode(BaseNode):
    def __init__(self, variable, iterable, body):
        super().__init__("for")
        self.variable = variable
        self.iterable = iterable
        self.body = body or []

    def match(self, other):
        if super().match(other) is None:
            return None

        match_result = {}
        matched_var = match_pattern(self.variable, other.variable)
        matched_iter = match_pattern(self.iterable, other.iterable)
        matched_body = match_list_pattern(self.body, other.body)

        if matched_var is None or matched_iter is None or matched_body is None:
            return None

        match_result.update(matched_var)
        match_result.update(matched_iter)
        match_result.update(matched_body)
        return match_result


class AssignNode(BaseNode):
    def __init__(self, variable, value):
        super().__init__("assign")
        self.variable = variable
        self.value = value

    def match(self, other):
        if super().match(other) is None:
            return None

        match_result = {}
        matched_var = match_pattern(self.variable, other.variable)
        matched_value = match_pattern(self.value, other.value)

        if matched_var is None or matched_value is None:
            return None

        match_result.update(matched_var)
        match_result.update(matched_value)
        return match_result


class CallNode(BaseNode):
    def __init__(self, function, args):
        super().__init__("call")
        self.function = function
        self.args = args or []

    def match(self, other):
        if super().match(other) is None:
            return None

        match_result = {}
        matched_func = match_pattern(self.function, other.function)
        matched_args = match_list_pattern(self.args, other.args)

        if matched_func is None or matched_args is None:
            return None

        match_result.update(matched_func)
        match_result.update(matched_args)
        return match_result

class UnaryOpNode(BaseNode):
    def __init__(self, op, operand):
        super().__init__("unary_op")
        self.op = op
        self.operand = operand

    def match(self, other):
        base_match = super().match(other)
        if base_match is None:
            return None

        matched_op = match_pattern(self.op, other.op)
        matched_operand = match_pattern(self.operand, other.operand)

        if matched_op is None or matched_operand is None:
            return None

        return {**base_match, **matched_op, **matched_operand}

# ✅ 패턴 매칭 유틸리티 함수
def match_pattern(pattern, value):
    """패턴을 적용하여 매칭된 변수 값을 딕셔너리로 반환"""
    if isinstance(pattern, str) and pattern.startswith("$"):
        return {pattern: value}  # 패턴 변수 저장
    elif isinstance(pattern, BaseNode):
        return pattern.match(value)  # 재귀적으로 매칭
    elif pattern == value:
        return {}  # 값이 동일하면 성공
    return None  # 매칭 실패


def match_list_pattern(pattern_list, value_list):
    # 둘 다 None인 경우 빈 매칭 결과 반환
    if pattern_list is None and value_list is None:
        return {}
    if not isinstance(pattern_list, list) or not isinstance(value_list, list):
        return None

    # 만약 패턴 리스트가 단 하나의 요소이고, 그 요소가 $변수라면,
    # 해당 변수에 전체 value_list를 캡처하도록 함.
    if len(pattern_list) == 1 and isinstance(pattern_list[0], str) and pattern_list[0].startswith("$"):
        return { pattern_list[0] : value_list }

    # 그렇지 않으면 길이가 동일해야 함
    if len(pattern_list) != len(value_list):
        return None

    result = {}
    for p, v in zip(pattern_list, value_list):
        matched = match_pattern(p, v)
        if matched is None:
            return None
        result.update(matched)
    return result

# ✅ 테스트 코드
if_pattern = IfNode("$cond", ["$body"])
if_code = IfNode("x > 10", ["print('Greater')"])
print(if_pattern.match(if_code))  # {'$cond': 'x > 10', '$body': ["print('Greater')"]}

binary_pattern = BinaryOpNode("$left", "+", "$right")
binary_code = BinaryOpNode("a", "+", "b")
print(binary_pattern.match(binary_code))  # {'$left': 'a', '$right': 'b'}

for_pattern = ForNode("$var", "$iter", ["$body"])
for_code = ForNode("i", "range(10)", ["print(i)"])
print(for_pattern.match(for_code))  # {'$var': 'i', '$iter': 'range(10)', '$body': ["print(i)"]}

assign_pattern = AssignNode("$var", "$value")
assign_code = AssignNode("x", "42")
print(assign_pattern.match(assign_code))  # {'$var': 'x', '$value': '42'}

call_pattern = CallNode("$func", ["$arg"])
call_code = CallNode("print", ["Hello"])
print(call_pattern.match(call_code))  # {'$func': 'print', '$arg': 'Hello'}


class MacroRule:
    def __init__(self, from_pattern, to_template):
        self.from_pattern = from_pattern  # 변환 전 패턴 (AST)
        self.to_template = to_template    # 변환 후 템플릿 (AST)

    def apply(self, node):
        """노드가 패턴과 매칭되면 변환된 AST 반환"""
        matched_values = self.from_pattern.match(node)
        if matched_values is None:
            return None  # 매칭되지 않으면 변환하지 않음
        
        return self.instantiate_template(self.to_template, matched_values)

    def instantiate_template(self, template, matched_values):
        """템플릿을 매칭된 값으로 채워 새 AST를 생성"""
        if isinstance(template, str) and template.startswith("$"):
            return matched_values.get(template, template)
        elif isinstance(template, BaseNode):
            new_attrs = {}
            for attr, value in template.__dict__.items():
                if attr == "type":
                    continue
                new_attrs[attr] = self.instantiate_template(value, matched_values)
            return template.__class__(**new_attrs)
        elif isinstance(template, list):
            # 만약 템플릿 리스트가 단 하나의 요소이고, 그 요소가 $변수라면, 
            # 매칭된 값을 그대로 반환 (즉, 리스트 중복 생성을 방지)
            if len(template) == 1 and isinstance(template[0], str) and template[0].startswith("$"):
                return matched_values.get(template[0], template)
            else:
                return [self.instantiate_template(item, matched_values) for item in template]
        return template

# unless 매크로 정의
unless_macro = MacroRule(
    IfNode("$cond", ["$body"]),  # 패턴
    IfNode(UnaryOpNode("not", "$cond"), ["$body"])  # 변환 후 AST
)

# 적용할 코드
code = IfNode("x > 10", ["print('Greater')"])

# 변환 수행
transformed = unless_macro.apply(code)
print("body:", code.body)
print("condition:", transformed.condition)
print("\top:", transformed.condition.op)
print("\toperand:", transformed.condition.operand)
print("body:", transformed.body)
print("else_body:", transformed.else_body)
