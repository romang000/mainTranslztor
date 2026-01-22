from .ast_nodes import *

class CSharpGenerator:
    def __init__(self):
        self.lines = []
        self.indent = 0

    def add(self, s):
        self.lines.append("    " * self.indent + s)

    # Вспомогательная функция для генерации значений или выражений
    def resolve(self, node):
        if isinstance(node, BinaryOp):
            # Если это сложение (1 + i) или ("Sum: " + sum)
            left = self.resolve_val(node.left)
            right = self.resolve_val(node.right)
            return f"{left} {node.op} {right}"
        return self.resolve_val(node)

    def resolve_val(self, val):
        if isinstance(val, str) and not val.isidentifier() and not val.isdigit():
             return f'"{val}"'
        return str(val)

    def visit(self, node):
        if isinstance(node, Program):
            self.add("using System;")
            for c in node.classes: self.visit(c)
        
        elif isinstance(node, ClassDecl):
            self.add(f"public class {node.name}"); self.add("{"); self.indent+=1
            for m in node.methods: self.visit(m)
            self.indent-=1; self.add("}")
        
        elif isinstance(node, MethodDecl):
            n = "Main" if node.name == "main" else node.name
            self.add(f"public static {node.return_type} {n}(string[] args)"); self.add("{"); self.indent+=1
            for s in node.body: self.visit(s)
            self.indent-=1; self.add("}")
        
        elif isinstance(node, VarDecl):
            t = "string" if node.var_type == "String" else node.var_type
            # Используем resolve для поддержки выражений (например, int sum = 0 + 1)
            val = self.resolve(node.value)
            self.add(f"{t} {node.name} = {val};")
            
        elif isinstance(node, Assignment): # <-- НОВЫЙ БЛОК
            val = self.resolve(node.value)
            self.add(f"{node.name} = {val};")
        
        elif isinstance(node, PrintStatement):
            val = self.resolve(node.expression)
            self.add(f"Console.WriteLine({val});")
        
        elif isinstance(node, UnaryOp):
            self.add(f"{node.expr}{node.op};")
        
        elif isinstance(node, ForLoop):
            init = f"{node.init.var_type} {node.init.name} = {self.resolve(node.init.value)}"
            cond = f"{node.condition.left} {node.condition.op} {node.condition.right}"
            upd = f"{node.update.expr}{node.update.op}"
            self.add(f"for ({init}; {cond}; {upd})"); self.add("{"); self.indent+=1
            for s in node.body: self.visit(s)
            self.indent-=1; self.add("}")
        
        elif isinstance(node, IfStatement):
            cond = f"{node.condition.left} {node.condition.op} {node.condition.right}"
            self.add(f"if ({cond})"); self.add("{"); self.indent+=1
            for s in node.true_body: self.visit(s)
            self.indent-=1; self.add("}")
            if node.false_body:
                self.add("else"); self.add("{"); self.indent+=1
                for s in node.false_body: self.visit(s)
                self.indent-=1; self.add("}")
        
        elif isinstance(node, WhileLoop):
            cond = f"{node.condition.left} {node.condition.op} {node.condition.right}"
            self.add(f"while ({cond})"); self.add("{"); self.indent+=1
            for s in node.body: self.visit(s)
            self.indent-=1; self.add("}")
        
        elif isinstance(node, DoWhileLoop):
            self.add("do"); self.add("{"); self.indent+=1
            for s in node.body: self.visit(s)
            self.indent-=1
            cond = f"{node.condition.left} {node.condition.op} {node.condition.right}"
            self.add(f"}} while ({cond});")

    def generate(self, tree):
        self.visit(tree)
        return "\n".join(self.lines)