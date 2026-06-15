"""
Research agent — tool execution and answer synthesis.

FIX: Added RESEARCH_PROMPT_WEB_AND_RAG for the case where both web and
RAG retrieval are needed. Previously, web_search always took precedence
and RAG results were silently dropped when requires_web_search was True.
"""

from langchain_core.messages import HumanMessage
from app.agents.base_agent import BaseAgent
from app.tools.web_search import web_search
from app.tools.retriever_tool import retriever_tool
from app.utils.prompt_templates import (
    RESEARCH_PROMPT_WEB,
    RESEARCH_PROMPT_RAG_ONLY,
    RESEARCH_PROMPT_WEB_AND_RAG,
    RESEARCH_PROMPT_KNOWLEDGE,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

_WEB_LIMIT = 5
_RAG_LIMIT = 6   # increased from 4 for better context coverage


def _format_web_results(snippets: list[str]) -> str:
    cleaned = [s.strip() for s in snippets[:_WEB_LIMIT] if s and s.strip()]
    if not cleaned:
        return "No web results found."
    return "\n\n".join(f"[{i+1}] {s}" for i, s in enumerate(cleaned))


def _format_rag_results(chunks: list[str]) -> str:
    cleaned = [c.strip() for c in chunks[:_RAG_LIMIT] if c and c.strip()]
    if not cleaned:
        return ""   # Return empty string so caller can detect "no RAG results"
    return "\n\n".join(f"[Doc {i+1}] {c}" for i, c in enumerate(cleaned))


class ResearchAgent(BaseAgent):

    async def run(
        self,
        input_text: str,
        requires_web_search: bool = False,
        requires_rag: bool = False,
    ) -> tuple[str, list[str]]:
        """
        Execute mandated tools and synthesise a grounded answer.

        Returns:
            (answer_string, tools_used_list)
        """
        logger.info(
            "ResearchAgent.run — web=%s  rag=%s  query=%r",
            requires_web_search, requires_rag, input_text,
        )

        tools_used: list[str] = []
        web_block = ""
        rag_block = ""

        # ── Tool execution — MANDATORY when flags are set ─────────────────────
        if requires_rag:
            logger.info("ResearchAgent — INVOKING retriever_tool")
            rag_raw = retriever_tool(input_text)
            rag_block = _format_rag_results(rag_raw)
            logger.info(
                "ResearchAgent — retriever returned %d chunks  block_len=%d",
                len(rag_raw), len(rag_block),
            )
            if rag_raw:
                tools_used.append("rag")
            else:
                logger.warning(
                    "ResearchAgent — retriever returned EMPTY results for %r. "
                    "Check: documents ingested? collection non-empty?", input_text,
                )

        if requires_web_search:
            logger.info("ResearchAgent — INVOKING Tavily web_search")
            web_raw = web_search(input_text)
            web_block = _format_web_results(web_raw)
            logger.info(
                "ResearchAgent — web_search returned %d snippets", len(web_raw)
            )
            if web_raw:
                tools_used.append("web_search")

        # ── Prompt selection ──────────────────────────────────────────────────
        if requires_web_search and requires_rag and rag_block:
            logger.info("ResearchAgent — route=WEB+RAG")
            prompt = RESEARCH_PROMPT_WEB_AND_RAG.format(
                rag_context=rag_block,
                web_results=web_block,
                query=input_text,
            )
        elif requires_web_search:
            logger.info("ResearchAgent — route=WEB_ONLY")
            prompt = RESEARCH_PROMPT_WEB.format(
                web_results=web_block,
                rag_context=rag_block or "No documents uploaded.",
                query=input_text,
            )
        elif requires_rag and rag_block:
            logger.info("ResearchAgent — route=RAG_ONLY")
            prompt = RESEARCH_PROMPT_RAG_ONLY.format(
                rag_context=rag_block,
                query=input_text,
            )
        elif requires_rag and not rag_block:
            # RAG was requested but retriever found nothing — tell LLM explicitly
            logger.warning("ResearchAgent — RAG requested but empty, using knowledge fallback")
            prompt = RESEARCH_PROMPT_KNOWLEDGE.format(query=input_text) + (
                "\n\nNote: The user may have uploaded a document but no relevant "
                "content was found. If this is a personal question, mention that "
                "you couldn't find the information in their uploaded documents."
            )
        else:
            logger.info("ResearchAgent — route=KNOWLEDGE")
            prompt = RESEARCH_PROMPT_KNOWLEDGE.format(query=input_text)

        # ── LLM synthesis ─────────────────────────────────────────────────────
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        answer = response.content.strip()

        logger.info(
            "ResearchAgent — answer_len=%d  tools_used=%s",
            len(answer), tools_used,
        )
        return answer, tools_used