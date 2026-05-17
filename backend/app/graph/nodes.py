"""
LangGraph node functions.

Node execution order:
    START → router_node
               │
               ├─ [math/date short-circuit] → END
               └─ [pipeline] → planner_node → research_node → critic_node → END

CRITICAL ARCHITECTURE RULES
────────────────────────────
1. router_node  — handles deterministic queries (math, date) without LLM.
2. planner_node — calls PlannerAgent to get JSON routing decision, writes
                  routing flags into AgentState. NEVER writes final_answer.
3. research_node — reads routing flags, EXECUTES the required tools, writes
                  answer. Tool calls are MANDATORY when flags are set.
4. critic_node  — refines answer, writes final_answer.
"""

import re
import json
from app.models.state_model import AgentState
from app.core.llm import get_llm
from app.agents.planner_agent import PlannerAgent
from app.agents.research_agent import ResearchAgent
from app.agents.critic_agent import CriticAgent
from app.tools.system_tools import get_current_date, calculate, solve_equations
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ── Regex patterns for deterministic routing ─────────────────────────────────

_DATE_TRIGGER:   frozenset[str] = frozenset({"date", "today", "what day"})
_DATE_BLOCKLIST: frozenset[str] = frozenset({
    "recent", "news", "latest", "update", "happened",
    "currently", "event", "story", "headline", "election",
})
_VAR_EQ_RE:    re.Pattern = re.compile(r"[a-zA-Z]\s*[+\-*/]?\s*[a-zA-Z0-9]*\s*=\s*[\d\-]")
_NUMERIC_RE:   re.Pattern = re.compile(r"\d+\s*[+\-*/]\s*\d+")
_SYMBOLIC_RE:  re.Pattern = re.compile(r"\b[a-zA-Z]\s*[+\-*/]\s*[a-zA-Z]\b")
_MATH_DIR_RE:  re.Pattern = re.compile(
    r"\b(solve|find|calculate|compute|evaluate|simplify)\b", re.IGNORECASE
)


def _is_date_intent(q: str) -> bool:
    ql = q.lower()
    return any(t in ql for t in _DATE_TRIGGER) and not any(b in ql for b in _DATE_BLOCKLIST)


def _is_math_intent(q: str) -> bool:
    return (
        bool(_VAR_EQ_RE.search(q))
        or bool(_NUMERIC_RE.search(q))
        or (bool(_SYMBOLIC_RE.search(q)) and bool(_MATH_DIR_RE.search(q)))
    )


def _extract_math_expression(q: str) -> str | None:
    if _VAR_EQ_RE.search(q):
        return q  # pass full string to solve_equations
    m = _NUMERIC_RE.search(q)
    return m.group(0).strip() if m else None


# ── Router node ───────────────────────────────────────────────────────────────

async def router_node(state: AgentState) -> AgentState:
    """
    Short-circuit deterministic queries without touching the LLM pipeline.

    Date and math queries are resolved here with 100% accuracy.
    All other queries fall through to the planner.
    """
    q = state["user_query"]
    ql = q.lower()
    logger.info("router_node — query: %r", q)

    # ── Date ─────────────────────────────────────────────────────────────────
    if _is_date_intent(ql):
        logger.info("router_node — route=DATE")
        result = get_current_date()
        return {
            **state,
            "final_answer":    result,
            "thinking_steps":  ["Checking current date"],
            "tools_used":      ["date"],
        }

    # ── Math / equations ──────────────────────────────────────────────────────
    if _is_math_intent(q):
        logger.info("router_node — route=MATH")
        expr = _extract_math_expression(q)
        if expr:
            if _VAR_EQ_RE.search(expr):
                result = solve_equations(expr)
            else:
                result = calculate(expr)
            if not result.startswith("Error"):
                return {
                    **state,
                    "final_answer":    result,
                    "thinking_steps":  ["Running calculations"],
                    "tools_used":      ["calculator"],
                }
            logger.warning("router_node — math failed: %s, falling through", result)

    # ── Fall through to full pipeline ─────────────────────────────────────────
    logger.info("router_node — route=PIPELINE")
    return state


# ── Planner node ──────────────────────────────────────────────────────────────

async def planner_node(state: AgentState) -> AgentState:
    """
    Run PlannerAgent to get a JSON routing decision.
    Writes routing flags and metadata into AgentState.
    Does NOT write final_answer.
    """
    logger.info("planner_node — START")
    llm = get_llm()
    agent = PlannerAgent(llm=llm)

    decision: dict = await agent.run(input_text=state["user_query"])

    logger.info(
        "planner_node — web=%s rag=%s plan=%r",
        decision["requires_web_search"],
        decision["requires_rag"],
        decision["plan"],
    )

    return {
        **state,
        "requires_web_search": decision["requires_web_search"],
        "requires_rag":        decision["requires_rag"],
        "plan":                decision["plan"],
        "thinking_steps":      decision.get("thinking_steps", []),
    }


# ── Research node ─────────────────────────────────────────────────────────────

async def research_node(state: AgentState) -> AgentState:
    """
    Execute the tools mandated by the Planner's routing decision.

    CRITICAL: tool calls here are not optional — if requires_web_search
    is True, Tavily WILL be invoked regardless of query content.
    """
    logger.info("research_node — START  web=%s rag=%s",
                state.get("requires_web_search"), state.get("requires_rag"))

    llm = get_llm()
    agent = ResearchAgent(llm=llm)

    answer, tools_used = await agent.run(
        input_text=state["user_query"],
        requires_web_search=state.get("requires_web_search", False),
        requires_rag=state.get("requires_rag", False),
    )

    logger.info("research_node — tools_used=%s  answer_len=%d", tools_used, len(answer))

    return {
        **state,
        "answer":     answer,
        "tools_used": list(set(state.get("tools_used", []) + tools_used)),
    }


# ── Critic node ───────────────────────────────────────────────────────────────

async def critic_node(state: AgentState) -> AgentState:
    """
    Refine the research answer. Write final_answer.
    """
    logger.info("critic_node — START")
    llm = get_llm()
    agent = CriticAgent(llm=llm)
    final_answer = await agent.run(input_text=state["answer"])
    logger.info("critic_node — final_len=%d", len(final_answer))
    return {**state, "final_answer": final_answer}