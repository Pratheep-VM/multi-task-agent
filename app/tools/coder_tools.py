import ast
import operator
import os

from mudraid import Agent
from langchain_core.tools import tool

coder_client = Agent(
    api_key_id=os.getenv("CODER_KEY_ID"),
    secret=os.getenv("CODER_SECRET")
)

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPERATORS:
        return _SAFE_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPERATORS:
        return _SAFE_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Unsafe operation: {type(node).__name__}")


@tool
def calculate_math(expression: str) -> str:
    """Evaluates mathematical expressions safely."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        return f"Math Result: {result}"
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"
