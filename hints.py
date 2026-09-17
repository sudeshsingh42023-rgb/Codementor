"""
hints.py — the "instructor" half of CodeMentor.

Two things live here:
  1. analyze_code(): a lightweight AST pass that detects patterns worth
     commenting on (nested loops, use of hash maps/sets/stacks) without
     executing the code.
  2. get_hint(): returns hints from a problem's hint ladder progressively —
     attempt 1 gets a nudge, attempt 2 gets the approach, attempt 3+ gets
     the near-solution. This mirrors how a human instructor avoids just
     handing over the answer on the first wrong attempt.

Swap-in point for later: replace `get_hint`'s static lookup with a call to
an LLM (e.g. the Claude API) that takes the student's actual code + the
failing test case and generates a hint tailored to their specific mistake,
still following the same "don't give the answer immediately" ladder.
"""

import ast


def analyze_code(code: str) -> dict:
    """Static analysis signals used for complexity/style feedback."""
    signals = {
        "has_nested_loop": False,
        "uses_dict": False,
        "uses_set": False,
        "uses_stack_pattern": False,  # list .append/.pop used together
        "loop_count": 0,
        "line_count": len(code.strip().splitlines()),
        "syntax_error": None,
    }
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        signals["syntax_error"] = f"Line {e.lineno}: {e.msg}"
        return signals

    def visit(node, depth_in_loop=0):
        is_loop = isinstance(node, (ast.For, ast.While))
        if is_loop:
            signals["loop_count"] += 1
            if depth_in_loop >= 1:
                signals["has_nested_loop"] = True
        for child in ast.iter_child_nodes(node):
            visit(child, depth_in_loop + 1 if is_loop else depth_in_loop)

    visit(tree)

    source_lower = code.lower()
    if "dict(" in source_lower or "{}" in code or ": {}" in code or "defaultdict" in source_lower:
        signals["uses_dict"] = True
    if "set(" in source_lower or " set()" in source_lower:
        signals["uses_set"] = True
    if ".append(" in code and ".pop(" in code:
        signals["uses_stack_pattern"] = True

    return signals


def get_hint(problem: dict, attempt_number: int) -> str:
    """attempt_number is 1-indexed (first submission = 1)."""
    ladder = problem["hints"]
    idx = min(attempt_number - 1, len(ladder) - 1)
    idx = max(idx, 0)
    return ladder[idx]


def complexity_feedback(problem: dict, signals: dict, all_passed: bool) -> str | None:
    """Flag a correct-but-inefficient solution, or praise a clean one."""
    if signals.get("syntax_error"):
        return None
    if not all_passed:
        return None

    ideal = problem.get("ideal_complexity", "")
    if ideal == "O(n)" and signals["has_nested_loop"]:
        return (
            f"All test cases pass, but nested loops usually mean O(n\u00b2) — "
            f"this problem has an {ideal} solution. "
            f"Look at whether a hash map or single pass could avoid the inner loop."
        )
    if ideal == "O(n)" and not signals["has_nested_loop"]:
        return "Correct, and it looks like a single pass — that's the O(n) solution this problem is looking for."
    return "All test cases pass."
