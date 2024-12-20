import json
import ast
import operator as op

# Supported operators
operators = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Mod: op.mod,
    ast.Pow: op.pow,
    ast.BitXor: op.xor,
    ast.USub: op.neg
}

def eval_expr(expr):
    """
    Evaluate a mathematical expression safely.
    """
    try:
        return _eval(ast.parse(expr, mode='eval').body)
    except Exception as e:
        return {"error": "Invalid expression"}

def _eval(node):
    if isinstance(node, ast.Num):  # <number>
        return node.n
    elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
        return operators[type(node.op)](_eval(node.left), _eval(node.right))
    elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
        return operators[type(node.op)](_eval(node.operand))
    else:
        raise TypeError(node)

def calculate(expression):
    """Evaluate a mathematical expression"""
    result = eval_expr(expression)
    return json.dumps({"result":result})

# Example usage
# print(calculate("1 + 2 * 3"))
