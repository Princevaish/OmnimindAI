"""
System-level utility tools: date, arithmetic calculator, and equation solver.

solve_equations() uses SymPy to handle:
    - Single equations:        "a + b = 10"
    - Systems of equations:    "a+b=10 and a-b=8 and b+c=6"
    - Mixed natural language:  "find c if a+b=10, a-b=8, b+c=6"

calculate() uses restricted eval() for simple numeric expressions:
    - "2 + 2 * 5"  →  "12"
    - "sqrt(144)"  →  "12"
"""

import re
import math
from datetime import datetime
from typing import Any

from sympy import symbols, Eq, solve, sympify, Symbol
from sympy.core.sympify import SympifyError
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# get_current_date
# ---------------------------------------------------------------------------

def get_current_date() -> str:
    """
    Return the current date as a human-readable formatted string.

    Returns:
        A string in the format: "Saturday, 21 March 2026"
    """
    return datetime.now().strftime("%A, %d %B %Y")


# ---------------------------------------------------------------------------
# calculate — restricted eval for pure numeric expressions
# ---------------------------------------------------------------------------

_SAFE_MATH_CONTEXT: dict[str, Any] = {
    "__builtins__": {},
    "abs": abs,
    "round": round,
    "pow": pow,
    "sqrt": math.sqrt,
    "ceil": math.ceil,
    "floor": math.floor,
    "log": math.log,
    "log10": math.log10,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "pi": math.pi,
    "e": math.e,
}


def calculate(expression: str) -> str:
    """
    Safely evaluate a numeric math expression and return the result as a string.

    Args:
        expression: A math expression string, e.g. "2 + 2 * 5" or "sqrt(16)".

    Returns:
        Result string (e.g. "12") or "Error: <reason>" on failure.
    """
    logger.debug("calculate — expression: %r", expression)

    if re.search(r"[a-zA-Z_]\w*\s*\.", expression):
        return "Error: attribute access is not allowed."

    try:
        result = eval(expression, _SAFE_MATH_CONTEXT, {})  # noqa: S307
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(result)
    except ZeroDivisionError:
        return "Error: division by zero."
    except (NameError, SyntaxError, TypeError, ValueError) as exc:
        return f"Error: {exc}"


# ---------------------------------------------------------------------------
# solve_equations — SymPy-based algebraic solver
# ---------------------------------------------------------------------------

# Patterns that identify equation strings
_EQ_SPLIT_RE: re.Pattern = re.compile(
    r"\band\b|,|;",
    re.IGNORECASE,
)

# Strip noise words that precede or follow equations
_NOISE_WORDS_RE: re.Pattern = re.compile(
    r"\b(find|solve|calculate|compute|evaluate|the|value|of|given|where|"
    r"if|what\s+is|let|assume|such\s+that)\b",
    re.IGNORECASE,
)

# A valid equation token: contains letters AND digits/operators AND one "="
_VALID_EQ_RE: re.Pattern = re.compile(
    r"[a-zA-Z].*=.*\d|\d.*=.*[a-zA-Z]|[a-zA-Z].*[+\-*/].*[a-zA-Z]"
)


def _parse_equations(raw: str) -> list[Eq]:
    """
    Parse a free-text string into a list of SymPy Eq objects.

    Strategy:
        1. Strip noise words ("find", "solve", "the value of", …).
        2. Split on "and", "," or ";" to get individual equation strings.
        3. For each token, split on "=" to get lhs and rhs.
        4. Use sympify() to convert both sides to SymPy expressions.
        5. Return list of Eq(lhs, rhs) objects.

    Args:
        raw: Raw user query or equation string.

    Returns:
        List of SymPy Eq objects. Empty list if parsing fails entirely.
    """
    # Step 1: remove noise
    cleaned: str = _NOISE_WORDS_RE.sub(" ", raw).strip()
    logger.debug("_parse_equations — cleaned: %r", cleaned)

    # Step 2: split into individual equation candidates
    tokens: list[str] = [t.strip() for t in _EQ_SPLIT_RE.split(cleaned) if t.strip()]
    logger.debug("_parse_equations — tokens: %s", tokens)

    equations: list[Eq] = []
    for token in tokens:
        if "=" not in token:
            logger.debug("_parse_equations — skipping (no =): %r", token)
            continue

        parts: list[str] = token.split("=", maxsplit=1)
        lhs_str: str = parts[0].strip()
        rhs_str: str = parts[1].strip()

        if not lhs_str or not rhs_str:
            continue

        try:
            lhs = sympify(lhs_str)
            rhs = sympify(rhs_str)
            equations.append(Eq(lhs, rhs))
            logger.debug("_parse_equations — parsed: Eq(%s, %s)", lhs, rhs)
        except (SympifyError, TypeError) as exc:
            logger.warning("_parse_equations — could not sympify %r: %s", token, exc)
            continue

    return equations


def _format_solution(solution: Any, target_var: Symbol | None) -> str:
    """
    Convert a SymPy solution into a clean output string.

    SymPy solve() return shapes:
        - List of values:   [5]           → "5"
        - Dict of values:   {a: 1, b: 9}  → "a = 1, b = 9"
        - List of dicts:    [{a:1, b:9}]  → "a = 1, b = 9"
        - Empty:            []            → "No solution found."

    Args:
        solution: Raw return value from sympy.solve().
        target_var: The specific variable asked for, if identifiable.

    Returns:
        Clean formatted string.
    """
    if not solution:
        return "No solution found."

    # List of dicts: [{a: 1, b: 9, c: 5}]
    if isinstance(solution, list) and solution and isinstance(solution[0], dict):
        sol_dict: dict = solution[0]
        if target_var and target_var in sol_dict:
            val = sol_dict[target_var]
            return str(int(val) if isinstance(val, float) and val == int(val) else val)
        parts = [f"{k} = {v}" for k, v in sorted(sol_dict.items(), key=lambda x: str(x[0]))]
        return ", ".join(parts)

    # Dict: {a: 1, b: 9}
    if isinstance(solution, dict):
        if target_var and target_var in solution:
            val = solution[target_var]
            return str(int(val) if isinstance(val, float) and val == int(val) else val)
        parts = [f"{k} = {v}" for k, v in sorted(solution.items(), key=lambda x: str(x[0]))]
        return ", ".join(parts)

    # List of values: [5]  (single variable solved)
    if isinstance(solution, list):
        if len(solution) == 1:
            val = solution[0]
            return str(int(val) if hasattr(val, "is_integer") and val.is_integer else val)
        return ", ".join(str(v) for v in solution)

    return str(solution)


def _identify_target_variable(raw: str, solved_vars: set) -> Symbol | None:
    """
    Identify which variable the user is asking for from the query.

    Looks for patterns like "find c", "value of c", "what is c".

    Args:
        raw:         Original user query.
        solved_vars: Set of Symbol objects from the solution.

    Returns:
        The target Symbol if identifiable, else None.
    """
    target_match = re.search(
        r"\b(?:find|solve\s+for|value\s+of|what\s+is)\s+([a-zA-Z])\b",
        raw,
        re.IGNORECASE,
    )
    if target_match:
        var_name: str = target_match.group(1)
        for sym in solved_vars:
            if str(sym) == var_name:
                return sym
    return None


def solve_equations(query: str) -> str:
    """
    Parse and solve a system of algebraic equations expressed in natural language.

    Supports:
        - Single equation:    "a + b = 10"
        - System:             "a+b=10 and a-b=8 and b+c=6"
        - With directives:    "find c given a+b=10, a-b=8, b+c=6"

    Args:
        query: Free-text query containing one or more equations.

    Returns:
        Clean solution string, e.g.:
            "5"           — single target variable
            "a = 1, b = 9, c = 5"  — full system solution
            "No solution found."   — unsolvable
            "Error: <reason>"      — parse failure

    Examples:
        >>> solve_equations("a+b=10 and a-b=8 and b+c=6")
        'a = 9, b = 1, c = 5'
        >>> solve_equations("find c if a+b=10, a-b=8, b+c=6")
        '5'
    """
    logger.info("solve_equations — query: %r", query)

    try:
        equations: list[Eq] = _parse_equations(query)

        if not equations:
            logger.warning("solve_equations — no equations parsed from: %r", query)
            return "Error: no equations found in the query."

        logger.info("solve_equations — parsed %d equation(s)", len(equations))

        # Collect all unique symbols across all equations
        all_symbols: set[Symbol] = set()
        for eq in equations:
            all_symbols.update(eq.free_symbols)

        logger.debug("solve_equations — symbols: %s", all_symbols)

        # Solve the system
        solution = solve(equations, list(all_symbols), dict=True)
        logger.info("solve_equations — raw solution: %s", solution)

        # Identify target variable if the user asked for a specific one
        target_var: Symbol | None = _identify_target_variable(query, all_symbols)
        logger.debug("solve_equations — target_var: %s", target_var)

        result: str = _format_solution(solution, target_var)
        logger.info("solve_equations — result: %r", result)
        return result

    except (SympifyError, TypeError, ValueError) as exc:
        logger.error("solve_equations — parse/solve error: %s", exc, exc_info=True)
        return f"Error: could not solve equations — {exc}"
    except Exception as exc:  # noqa: BLE001
        logger.error("solve_equations — unexpected error: %s", exc, exc_info=True)
        return f"Error: unexpected failure — {exc}"