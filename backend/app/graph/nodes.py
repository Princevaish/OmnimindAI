"""
LangGraph node functions — one intelligent router plus one node per agent stage.

Router logic (evaluated in priority order, first match wins):
    1. Equation system intent — variables + "=" + operators or solve directive
                                → solve_equations() → set final_answer, skip pipeline
    2. Arithmetic intent      — numeric expression with operators
                                → calculate() → set final_answer, skip pipeline
    3. Date intent            — "date/today" NOT combined with news keywords
                                → get_current_date() → set final_answer, skip pipeline
    4. No match               — return state unchanged, full agent pipeline runs

Agent node contract:
    - Receives full AgentState.
    - Instantiates its agent with a fresh LLM handle.
    - Writes exactly one new field into state.
    - Returns updated state via immutable spread: {**state, "key": value}.
"""

import re
from app.models.state_model import AgentState
from app.core.llm import get_llm
from app.agents.planner_agent import PlannerAgent
from app.agents.research_agent import ResearchAgent
from app.agents.critic_agent import CriticAgent
from app.tools.system_tools import get_current_date, calculate, solve_equations
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Intent detection — compiled at import time
# ---------------------------------------------------------------------------

# ── Equation detection ──────────────────────────────────────────────────────

# Matches "variable = something" or "something = variable"
_VAR_EQ_RE: re.Pattern = re.compile(
    r"[a-zA-Z]\s*[+\-*/]?\s*[a-zA-Z0-9]*\s*=\s*[\d\-]",  # a+b=10, a=5
)

# Matches "variable op variable" without digits — pure symbolic expression
_SYMBOLIC_RE: re.Pattern = re.compile(
    r"\b[a-zA-Z]\s*[+\-*/]\s*[a-zA-Z]\b"                  # a+b, x-y
)

# Solve/find directive that implies an equation context
_SOLVE_DIRECTIVE_RE: re.Pattern = re.compile(
    r"\b(solve|find|calculate|compute|evaluate|simplify)\b",
    re.IGNORECASE,
)

# Must have at least one letter variable AND one "=" to be an equation query
_CONTAINS_LETTER_RE: re.Pattern = re.compile(r"[a-zA-Z]")
_CONTAINS_EQUALS_RE: re.Pattern = re.compile(r"=")

# ── Arithmetic detection ────────────────────────────────────────────────────

# Pure numeric expression with operator
_NUMERIC_EXPR_RE: re.Pattern = re.compile(
    r"\d+\s*[+\-*/]\s*\d+"
)

# Natural-language operators
_NL_OPERATOR_RE: re.Pattern = re.compile(
    r"\b(\d+)\s+(divided\s+by|multiplied\s+by|times|plus|minus)\s+(\d+)\b",
    re.IGNORECASE,
)

# ── Date detection ──────────────────────────────────────────────────────────

_DATE_TRIGGER: frozenset[str] = frozenset({"date", "today", "what day"})
_DATE_BLOCKLIST: frozenset[str] = frozenset({
    "recent", "news", "latest", "update", "happened",
    "currently", "event", "story", "headline",
})


# ---------------------------------------------------------------------------
# Intent classifiers
# ---------------------------------------------------------------------------

def _is_equation_intent(query: str) -> bool:
    """
    Return True when the query expresses an algebraic equation or system.

    Detection criteria (any one sufficient):
        A) Contains "variable = digit" pattern         → "a+b=10", "x=5"
        B) Contains symbolic expression ("a+b")
           AND a solve directive OR "=" sign            → "find a+b=10"
        C) Contains a solve directive AND a variable
           AND an "=" sign                              → "solve for c if a-b=3"

    Args:
        query: Raw user query.

    Returns:
        True if query should be routed to solve_equations().
    """
    has_letter: bool = bool(_CONTAINS_LETTER_RE.search(query))
    has_equals: bool = bool(_CONTAINS_EQUALS_RE.search(query))
    has_var_eq: bool = bool(_VAR_EQ_RE.search(query))
    has_symbolic: bool = bool(_SYMBOLIC_RE.search(query))
    has_directive: bool = bool(_SOLVE_DIRECTIVE_RE.search(query))

    # Case A: explicit variable equation
    if has_var_eq:
        logger.debug("equation_intent=A (var=digit pattern)")
        return True

    # Case B: symbolic expression with equals or directive
    if has_symbolic and (has_equals or has_directive):
        logger.debug("equation_intent=B (symbolic + equals/directive)")
        return True

    # Case C: directive + variable + equals
    if has_directive and has_letter and has_equals:
        logger.debug("equation_intent=C (directive + letter + equals)")
        return True

    return False


def _is_arithmetic_intent(query: str) -> bool:
    """
    Return True when the query is a pure numeric arithmetic expression.
    Does NOT fire for algebraic equations (those are caught above).

    Args:
        query: Raw user query.

    Returns:
        True if query should be routed to calculate().
    """
    if _NUMERIC_EXPR_RE.search(query):
        logger.debug("arithmetic_intent=numeric_expr")
        return True
    if _NL_OPERATOR_RE.search(query):
        logger.debug("arithmetic_intent=nl_operator")
        return True
    return False


def _normalise_nl_arithmetic(query: str) -> str:
    """
    Replace natural-language operator words with symbols for calculate().

    Args:
        query: User query possibly containing "divided by", "times", etc.

    Returns:
        String with NL operator words replaced by arithmetic symbols.
    """
    nl_map = [
        (r"\bdivided\s+by\b",    "/"),
        (r"\bmultiplied\s+by\b", "*"),
        (r"\btimes\b",           "*"),
        (r"\bplus\b",            "+"),
        (r"\bminus\b",           "-"),
    ]
    result: str = query
    for pattern, symbol in nl_map:
        result = re.sub(pattern, symbol, result, flags=re.IGNORECASE)
    return result


def _extract_numeric_expression(query: str) -> str | None:
    """
    Extract the first calculable numeric sub-expression from the query.

    Args:
        query: Raw or NL-normalised user query.

    Returns:
        Expression string ready for calculate(), or None.
    """
    normalised: str = _normalise_nl_arithmetic(query)
    match = _NUMERIC_EXPR_RE.search(normalised)
    if match:
        return match.group(0).strip()
    return None


def _is_date_intent(query_lower: str) -> bool:
    """
    Return True only when the query asks for the current date/day,
    and is NOT a news or recency query.

    Args:
        query_lower: Lowercased user query.

    Returns:
        True if date tool should be triggered.
    """
    has_trigger = any(token in query_lower for token in _DATE_TRIGGER)
    has_block = any(word in query_lower for word in _DATE_BLOCKLIST)
    return has_trigger and not has_block


# ---------------------------------------------------------------------------
# Router node
# ---------------------------------------------------------------------------

async def router_node(state: AgentState) -> AgentState:
    """
    Inspect the user query and short-circuit the pipeline when a tool applies.

    Routing priority:
        1. Equation system → solve_equations() → final_answer
        2. Arithmetic      → calculate()       → final_answer
        3. Date            → get_current_date() → final_answer
        4. Fall-through    → state unchanged, full pipeline runs

    On tool errors (result starts with "Error:"), the router logs a warning
    and falls through to the full pipeline rather than returning a raw error
    string as the final answer.

    Reads:  state["user_query"]
    Writes: state["final_answer"]  — only when a route matches cleanly.

    Args:
        state: Current pipeline state.

    Returns:
        Updated state with "final_answer" set (short-circuit),
        or original state unchanged (pipeline continues).
    """
    raw_query: str = state["user_query"]
    query_lower: str = raw_query.lower()

    logger.info("router_node — evaluating: %r", raw_query)

    # ── Rule 1: Equation system ─────────────────────────────────────────────
    if _is_equation_intent(raw_query):
        logger.info("router_node — route=EQUATION_SOLVER")
        result: str = solve_equations(raw_query)
        logger.info("router_node — solver result: %r", result)

        if not result.startswith("Error"):
            return {**state, "final_answer": result}

        logger.warning(
            "router_node — solver failed (%s), falling through to pipeline", result
        )

    # ── Rule 2: Arithmetic expression ───────────────────────────────────────
    elif _is_arithmetic_intent(raw_query):
        logger.info("router_node — route=CALCULATOR")
        expression: str | None = _extract_numeric_expression(raw_query)

        if expression:
            logger.info("router_node — expression: %r", expression)
            calc_result: str = calculate(expression)
            logger.info("router_node — calc result: %r", calc_result)

            if not calc_result.startswith("Error"):
                return {**state, "final_answer": calc_result}

            logger.warning(
                "router_node — calculate failed (%s), falling through", calc_result
            )
        else:
            logger.warning("router_node — arithmetic intent but no expression extracted")

    # ── Rule 3: Date ────────────────────────────────────────────────────────
    if _is_date_intent(query_lower):
        logger.info("router_node — route=DATE")
        return {**state, "final_answer": get_current_date()}

    # ── Rule 4: Full pipeline ───────────────────────────────────────────────
    logger.info("router_node — route=PIPELINE")
    return state


# ---------------------------------------------------------------------------
# Agent nodes
# ---------------------------------------------------------------------------

async def planner_node(state: AgentState) -> AgentState:
    """
    Execute PlannerAgent and store the reasoning plan in state.

    Reads:  state["user_query"]
    Writes: state["plan"]
    """
    logger.info("planner_node — START")
    llm = get_llm()
    agent = PlannerAgent(llm=llm)
    plan: str = await agent.run(input_text=state["user_query"])
    logger.info("planner_node — COMPLETE  length=%d", len(plan))
    return {**state, "plan": plan}


async def research_node(state: AgentState) -> AgentState:
    """
    Execute ResearchAgent and store the grounded answer in state.

    Reads:  state["user_query"]
    Writes: state["answer"]
    """
    logger.info("research_node — START")
    llm = get_llm()
    agent = ResearchAgent(llm=llm)
    answer: str = await agent.run(input_text=state["user_query"])
    logger.info("research_node — COMPLETE  length=%d", len(answer))
    return {**state, "answer": answer}


async def critic_node(state: AgentState) -> AgentState:
    """
    Execute CriticAgent and store the refined answer in state.

    Reads:  state["answer"]
    Writes: state["final_answer"]
    """
    logger.info("critic_node — START")
    llm = get_llm()
    agent = CriticAgent(llm=llm)
    final_answer: str = await agent.run(input_text=state["answer"])
    logger.info("critic_node — COMPLETE  length=%d", len(final_answer))
    return {**state, "final_answer": final_answer}
