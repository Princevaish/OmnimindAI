"""
Research agent that conditionally routes between real-time web search
and RAG-based retrieval depending on query intent.

Routing logic:
    REALTIME query  → web_search() → strong forcing prompt → LLM
    KNOWLEDGE query → retriever_tool() → standard context prompt → LLM

Prompt design:
    Real-time prompt uses imperative language ("You MUST") to override the
    LLM's default behaviour of falling back to parametric/training knowledge
    when web snippets conflict with what it already knows.
    Knowledge prompt is softer — the LLM's internal knowledge is the
    intended source, so no forcing language is needed.
"""

from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from app.agents.base_agent import BaseAgent
from app.tools.retriever_tool import retriever_tool
from app.tools.web_search import web_search

# ---------------------------------------------------------------------------
# Real-time intent detection
# ---------------------------------------------------------------------------

REALTIME_KEYWORDS: list[str] = [
    "latest", "recent", "today", "current", "now",
    "news", "update", "breaking", "happening", "live",
    "ongoing", "tonight", "yesterday", "this week",
    "this month", "just", "newly", "emerged",
]

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

# Used when web results are available — imperative framing forces the LLM
# to treat retrieved snippets as ground truth rather than a soft suggestion.
_WEB_PROMPT_TEMPLATE: str = """You are a research assistant with access to live web search results.

STRICT RULES:
- You MUST base your answer on the Web Results provided below.
- Do NOT rely on your training knowledge for facts, dates, or events.
- If the web results contain relevant information, use it directly.
- If the web results are insufficient, say so clearly — do not invent facts.
- Answer concisely and directly. Do not mention "web search" in your response.

Web Results:
{web_results}

Query:
{query}

Answer:"""

# Used when the query is knowledge-based — no real-time data needed.
_KNOWLEDGE_PROMPT_TEMPLATE: str = """You are a knowledgeable research assistant.

Answer the following query using your own knowledge.
Be accurate, concise, and direct. Do not speculate beyond what you know.

Query:
{query}

Answer:"""

# Used when web was attempted but returned nothing — RAG fills the gap.
_RAG_FALLBACK_PROMPT_TEMPLATE: str = """You are a research assistant.

Answer the query using the context below.
If the context is insufficient, use your own knowledge and say so.

Context:
{rag_context}

Query:
{query}

Answer:"""

_web_prompt = PromptTemplate(
    input_variables=["web_results", "query"],
    template=_WEB_PROMPT_TEMPLATE,
)

_knowledge_prompt = PromptTemplate(
    input_variables=["query"],
    template=_KNOWLEDGE_PROMPT_TEMPLATE,
)

_rag_fallback_prompt = PromptTemplate(
    input_variables=["rag_context", "query"],
    template=_RAG_FALLBACK_PROMPT_TEMPLATE,
)

# ---------------------------------------------------------------------------
# Result formatting helpers
# ---------------------------------------------------------------------------

_WEB_RESULT_LIMIT: int = 5
_RAG_CHUNK_LIMIT: int = 4


def _is_realtime_query(query: str) -> bool:
    """
    Determine whether a query requires real-time web data.

    Checks every keyword and two-word phrase in REALTIME_KEYWORDS against
    the lowercased query. Using `in` rather than word-boundary matching
    intentionally catches compound forms like "currently", "updated", etc.

    Args:
        query: Raw user query string.

    Returns:
        True if any real-time keyword is found in the lowercased query.
    """
    query_lower: str = query.lower()
    return any(keyword in query_lower for keyword in REALTIME_KEYWORDS)


def _format_web_results(raw: list[str], limit: int = _WEB_RESULT_LIMIT) -> str:
    """
    Number and join web snippets so the LLM can reference them discretely.

    Numbered formatting ("1. …  2. …") gives the LLM a clearer signal that
    these are distinct sources rather than one continuous paragraph, which
    produces more accurate attribution in the response.

    Args:
        raw:   List of snippet strings from web_search().
        limit: Maximum number of snippets to include.

    Returns:
        Numbered multi-line string, or an empty string if raw is empty.
    """
    cleaned: list[str] = [
        s.strip() for s in raw[:limit] if s and s.strip()
    ]
    if not cleaned:
        return ""
    return "\n".join(f"{i + 1}. {snippet}" for i, snippet in enumerate(cleaned))


def _format_rag_results(raw: list[str]) -> str:
    """
    Join RAG document chunks into a single context block.

    Args:
        raw: page_content strings from the vector store.

    Returns:
        Double-newline-joined string, or empty string if raw is empty.
    """
    cleaned: list[str] = [c.strip() for c in raw if c and c.strip()]
    return "\n\n".join(cleaned) if cleaned else ""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class ResearchAgent(BaseAgent):
    """
    Agent that routes queries to the correct retrieval strategy and
    constructs a forcing prompt that ensures the LLM uses retrieved
    context rather than falling back to stale parametric knowledge.

    Routing decision tree:
        ┌─ is_realtime_query? ──YES──► web_search()
        │                              ├─ results? ──YES──► WEB prompt   → LLM
        │                              └─ empty?   ──YES──► RAG fallback → LLM
        └──────────────────── NO  ──► retriever_tool()
                                       ├─ results? ──YES──► RAG fallback → LLM
                                       └─ empty?   ──YES──► KNOWLEDGE    → LLM
    """

    async def run(self, input_text: str) -> str:
        """
        Select retrieval strategy, build the appropriate prompt, invoke LLM.

        Args:
            input_text: Raw user query.

        Returns:
            Clean answer string from the LLM.
        """
        use_web: bool = _is_realtime_query(input_text)

        print(f"[ResearchAgent] query: {input_text!r}")
        print(f"[ResearchAgent] realtime_query={use_web}")

        # ------------------------------------------------------------------
        # Branch A — real-time query: web search first
        # ------------------------------------------------------------------
        if use_web:
            web_raw: list[str] = web_search(input_text)
            web_block: str = _format_web_results(web_raw)

            if web_block:
                # Web results exist → use strong forcing prompt
                print(f"[ResearchAgent] route=WEB  snippets={len(web_raw)}")
                formatted_prompt: str = _web_prompt.format(
                    web_results=web_block,
                    query=input_text,
                )
                return await self._invoke_llm(formatted_prompt)

            # Web returned nothing → fall through to RAG
            print("[ResearchAgent] web empty — falling back to RAG")
            rag_raw: list[str] = retriever_tool(input_text)
            rag_block: str = _format_rag_results(rag_raw)

            if rag_block:
                print(f"[ResearchAgent] route=RAG-FALLBACK  chunks={len(rag_raw)}")
                formatted_prompt = _rag_fallback_prompt.format(
                    rag_context=rag_block,
                    query=input_text,
                )
                return await self._invoke_llm(formatted_prompt)

            # Both empty → knowledge-only (still better than an error)
            print("[ResearchAgent] route=KNOWLEDGE (web+RAG both empty)")
            formatted_prompt = _knowledge_prompt.format(query=input_text)
            return await self._invoke_llm(formatted_prompt)

        # ------------------------------------------------------------------
        # Branch B — knowledge query: RAG first, knowledge fallback
        # ------------------------------------------------------------------
        rag_raw = retriever_tool(input_text)
        rag_block = _format_rag_results(rag_raw)

        if rag_block:
            print(f"[ResearchAgent] route=RAG  chunks={len(rag_raw)}")
            formatted_prompt = _rag_fallback_prompt.format(
                rag_context=rag_block,
                query=input_text,
            )
            return await self._invoke_llm(formatted_prompt)

        print("[ResearchAgent] route=KNOWLEDGE (RAG empty)")
        formatted_prompt = _knowledge_prompt.format(query=input_text)
        return await self._invoke_llm(formatted_prompt)

    async def _invoke_llm(self, prompt: str) -> str:
        """
        Wrap a formatted prompt string in a HumanMessage and invoke the LLM.

        Extracted as a private method to keep the routing logic in run()
        free of LangChain message construction boilerplate.

        Args:
            prompt: Fully formatted prompt string ready for the LLM.

        Returns:
            Raw LLM response content string.
        """
        messages = [HumanMessage(content=prompt)]
        response = await self.llm.ainvoke(messages)
        return response.content