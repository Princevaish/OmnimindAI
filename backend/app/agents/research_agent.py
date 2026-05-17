"""
Research agent — tool execution and answer synthesis.

ROLE CONTRACT
─────────────
The Research agent EXECUTES the tools that the Planner decided to use.
It does NOT decide which tools to call — that decision lives in AgentState
(requires_web_search, requires_rag) written by the Planner.

Tool execution is MANDATORY when the corresponding flag is set — the
forcing prompt ensures the LLM uses retrieved content rather than
falling back to parametric knowledge.
"""

from langchain_core.messages import HumanMessage
from app.agents.base_agent import BaseAgent
from app.tools.web_search import web_search
from app.tools.retriever_tool import retriever_tool
from app.utils.prompt_templates import (
    RESEARCH_PROMPT_WEB,
    RESEARCH_PROMPT_RAG_ONLY,
    RESEARCH_PROMPT_KNOWLEDGE,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

_WEB_LIMIT = 5
_RAG_LIMIT = 4


def _format_web_results(snippets: list[str]) -> str:
    """Number and join web snippets for clear LLM attribution."""
    cleaned = [s.strip() for s in snippets[:_WEB_LIMIT] if s and s.strip()]
    if not cleaned:
        return "No web results found."
    return "\n\n".join(f"[{i+1}] {s}" for i, s in enumerate(cleaned))


def _format_rag_results(chunks: list[str]) -> str:
    """Join RAG chunks into a labelled context block."""
    cleaned = [c.strip() for c in chunks[:_RAG_LIMIT] if c and c.strip()]
    return "\n\n".join(cleaned) if cleaned else "No relevant documents found."


class ResearchAgent(BaseAgent):
    """
    Executes tools based on routing flags in AgentState, then synthesises
    a grounded answer using the appropriate prompt variant.
    """

    async def run(
        self,
        input_text: str,
        requires_web_search: bool = False,
        requires_rag: bool = False,
    ) -> tuple[str, list[str]]:
        """
        Execute tools and synthesise a grounded answer.

        Args:
            input_text:          The user query.
            requires_web_search: If True, Tavily MUST be invoked.
            requires_rag:        If True, vector retrieval MUST be invoked.

        Returns:
            Tuple of (answer_string, tools_used_list).
        """
        logger.info(
            "ResearchAgent — web=%s rag=%s query=%r",
            requires_web_search, requires_rag, input_text,
        )

        tools_used: list[str] = []
        web_block = ""
        rag_block = ""

        # ── Tool execution ───────────────────────────────────────────────────
        if requires_web_search:
            logger.info("ResearchAgent — INVOKING Tavily web_search")
            web_raw = web_search(input_text)
            web_block = _format_web_results(web_raw)
            logger.info("ResearchAgent — web_search returned %d snippets", len(web_raw))
            if web_raw:
                tools_used.append("web_search")

        if requires_rag:
            logger.info("ResearchAgent — INVOKING retriever_tool")
            rag_raw = retriever_tool(input_text)
            rag_block = _format_rag_results(rag_raw)
            logger.info("ResearchAgent — retriever returned %d chunks", len(rag_raw))
            if rag_raw:
                tools_used.append("rag")

        # ── Prompt selection ─────────────────────────────────────────────────
        if requires_web_search:
            # Web results present — use forcing prompt
            prompt = RESEARCH_PROMPT_WEB.format(
                web_results=web_block,
                rag_context=rag_block or "None",
                query=input_text,
            )
        elif requires_rag:
            prompt = RESEARCH_PROMPT_RAG_ONLY.format(
                rag_context=rag_block,
                query=input_text,
            )
        else:
            # No retrieval needed — knowledge-only
            prompt = RESEARCH_PROMPT_KNOWLEDGE.format(query=input_text)

        # ── LLM synthesis ────────────────────────────────────────────────────
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        answer = response.content.strip()

        logger.info("ResearchAgent — answer length: %d chars", len(answer))
        return answer, tools_used