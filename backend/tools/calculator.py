"""
Safe math evaluation using ast — no eval(), no imports, no function calls.
"""

import ast
import operator
import re

from core.logging_config import get_logger

logger = get_logger("tools")

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
}

_ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _normalize_expression(expression: str) -> str:
    """Clean common natural-language prefixes from calculator input."""
    expr = expression.strip()
    expr = re.sub(r"^(what is|calculate|compute)\s+", "", expr, flags=re.I)
    return expr.strip()


def safe_calculate(expression: str) -> float:
    """
    Evaluate a math expression safely.

    Supported: + - * / % ** () and floats/negatives.
    Raises ValueError on invalid or unsafe input.
    """
    expr = _normalize_expression(expression)
    if not expr:
        raise ValueError("Empty expression.")

    # Reject anything that looks like code
    forbidden = ("import", "__", "lambda", "exec", "eval", "open", "[", "]", "{", "}")
    lowered = expr.lower()
    for token in forbidden:
        if token in lowered:
            raise ValueError(f"Forbidden token in expression: {token}")

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression syntax: {exc}") from exc

    def _eval_node(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError("Only numeric constants are allowed.")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_BINOPS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            return float(_ALLOWED_BINOPS[op_type](left, right))

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _ALLOWED_UNARYOPS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            return float(_ALLOWED_UNARYOPS[op_type](_eval_node(node.operand)))

        raise ValueError(
            f"Unsupported expression element: {type(node).__name__}"
        )

    result = _eval_node(tree)
    logger.info("Calculator evaluated expression successfully")
    return result


def calculator_tool(expression: str) -> str:
    """Tool API — same signature as before."""
    try:
        result = safe_calculate(expression)
        if result == int(result):
            return f"Result: {int(result)}"
        return f"Result: {result}"
    except Exception as e:
        logger.warning("Calculator error: %s", e)
        return f"Error: {str(e)}"
