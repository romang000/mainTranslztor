class ASTNode: pass

class Program(ASTNode):
    def __init__(self, classes): self.classes = classes

class ClassDecl(ASTNode):
    def __init__(self, name, methods): self.name = name; self.methods = methods

class MethodDecl(ASTNode):
    def __init__(self, name, ret, args, body):
        self.name = name; self.return_type = ret; self.args = args; self.body = body

class MethodParam(ASTNode):
    def __init__(self, param_type, name, is_array=False):
        self.param_type = param_type; self.name = name; self.is_array = is_array

class Assignment(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class VarDecl(ASTNode):
    def __init__(self, t, n, v): self.var_type = t; self.name = n; self.value = v

class PrintStatement(ASTNode):
    def __init__(self, expr): self.expression = expr

class BinaryOp(ASTNode): 
    def __init__(self, left, op, right): self.left = left; self.op = op; self.right = right

class UnaryOp(ASTNode): 
    def __init__(self, expr, op): self.expr = expr; self.op = op

class FunctionCall(ASTNode):
    def __init__(self, name, args): self.name = name; self.args = args

class ReturnStatement(ASTNode):
    def __init__(self, expr): self.expression = expr

class ForLoop(ASTNode):
    def __init__(self, init, condition, update, body):
        self.init = init; self.condition = condition; self.update = update; self.body = body

class IfStatement(ASTNode):
    def __init__(self, condition, true_body, false_body=None):
        self.condition = condition; self.true_body = true_body; self.false_body = false_body

class WhileLoop(ASTNode):
    def __init__(self, condition, body): self.condition = condition; self.body = body

class DoWhileLoop(ASTNode):
    def __init__(self, body, condition): self.body = body; self.condition = condition