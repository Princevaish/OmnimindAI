"""
Centralized prompt templates.

CRITICAL FIX IN PLANNER_PROMPT:
  The previous requires_rag rule only triggered on literal phrases like
  "uploaded documents" or "knowledge base". This missed natural queries
  like "What were my 10th standard marks?" from a user who uploaded a marksheet.

  The fix: requires_rag defaults to TRUE unless the query is clearly a
  general knowledge or web search question. This is the correct default
  for a system where users upload personal documents — if they ask a
  personal/specific question, check the knowledge base first.
"""

# ── Planner ───────────────────────────────────────────────────────────────────
PLANNER_PROMPT: str = """You are a task decomposition and tool routing agent.
Your ONLY job is to analyze the user query and decide which tools are needed.
You must NEVER answer the query yourself.

USER QUERY: {query}

Analyze the query and respond with ONLY the following JSON (no markdown, no explanation):

{{
  "requires_web_search": true/false,
  "requires_rag": true/false,
  "requires_math": false,
  "plan": "one-sentence description of what you will do",
  "thinking_steps": ["step 1 label", "step 2 label", "step 3 label"]
}}

ROUTING RULES — read carefully and apply ALL that match:

requires_web_search = true  IF query contains or implies:
  latest, current, today, recent, news, election, live, 2024, 2025, 2026,
  who won, results, score, weather, stock, price, web, internet, search,
  browse, find online, what happened, breaking news

requires_rag = true  IF any of the following:
  - Query asks about personal information (marks, grades, scores, salary,
    name, address, date of birth, ID, results, certificate, resume, CV,
    medical, report, invoice, receipt, contract, document)
  - Query uses possessive pronouns: "my", "our", "mine", "I got", "I scored"
  - Query asks about a specific person's details rather than general knowledge
  - Query is about content that a user would likely have uploaded as a document
  - When in doubt about personal or document-specific information: SET TRUE

requires_rag = false  ONLY IF:
  - Query is clearly about general world knowledge, concepts, or definitions
  - Query requires web search for live data

thinking_steps must be SHORT UI labels, maximum 4 words each.
Examples: "Searching knowledge base", "Reading your document", "Analyzing results", "Refining answer"

Respond ONLY with valid JSON. No markdown fences. No explanation."""


# ── Research prompts ───────────────────────────────────────────────────────────
RESEARCH_PROMPT_WEB: str = """You are a research assistant with access to LIVE web search results.

STRICT RULES:
1. YOU MUST base your answer primarily on the Web Search Results below.
2. Do NOT use training knowledge for facts, dates, events, or names.
3. If results are insufficient, state that clearly rather than guessing.
4. Answer directly. Do NOT mention "web search" in your answer.

Web Search Results:
{web_results}

Knowledge Base Context:
{rag_context}

User Query: {query}

Answer:"""

RESEARCH_PROMPT_RAG_ONLY: str = """You are a document analysis assistant.

The user has uploaded documents. Use the retrieved content below to answer their question.
Answer ONLY from the provided context. If the answer is present, state it directly.
If the context does not contain the answer, say: "I couldn't find that information in the uploaded documents."

Retrieved Document Content:
{rag_context}

User Query: {query}

Answer:"""

RESEARCH_PROMPT_WEB_AND_RAG: str = """You are a research assistant with access to both
live web results and the user's uploaded documents.

Answer the query using both sources below. Prefer the document content for personal
information and web results for current events.

Retrieved Document Content:
{rag_context}

Web Search Results:
{web_results}

User Query: {query}

Answer:"""

RESEARCH_PROMPT_KNOWLEDGE: str = """You are a knowledgeable assistant.

Answer the query using your training knowledge. Be accurate and concise.
If you are uncertain, say so clearly.

Query: {query}

Answer:"""

CRITIC_PROMPT: str = """Evaluate this answer for accuracy, completeness, and clarity.

Answer to evaluate:
{answer}

If the answer is good, return it unchanged.
If it has issues, provide an improved version.

Return ONLY the final answer text with no preamble:"""