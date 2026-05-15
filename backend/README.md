<div align="center">

# ⬡ OmniMind AI

### Production-Grade Multi-Agent Decision Intelligence System

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.1+-FF6B35?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**OmniMind AI** is an advanced multi-agent AI system that orchestrates a pipeline of specialized LLM agents — Planner, Research, and Critic — to deliver reasoned, grounded, and refined answers to complex queries. Built on LangGraph, FastAPI, RAG, and real-time WebSocket streaming, the system makes the AI reasoning process visible, auditable, and production-deployable.

[Architecture](#-system-architecture) · [Setup](#-installation) · [API Reference](#-api-endpoints) · [Deployment](#-docker--devops) · [Contributing](#-contributing)

</div>

---

## Table of Contents

- [Why This Project Is Different](#-why-this-project-is-different)
- [Key Engineering Challenges Solved](#-key-engineering-challenges-solved)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Multi-Agent Workflow](#-multi-agent-workflow)
- [GenAI Concepts](#-genai-concepts-used)
- [RAG Pipeline](#-rag-pipeline)
- [WebSocket Streaming Architecture](#-websocket--streaming-architecture)
- [Backend Architecture](#-backend-architecture)
- [Frontend Architecture](#-frontend-architecture)
- [Database Design](#-database-design)
- [Docker & DevOps](#-docker--devops)
- [Scalability Considerations](#-scalability-considerations)
- [Security Considerations](#-security-considerations)
- [Tech Stack](#-tech-stack)
- [API Endpoints](#-api-endpoints)
- [Project Structure](#-project-structure)
- [Installation](#-installation)
- [Running Locally](#-running-locally)
- [Screenshots](#-screenshots)
- [Future Improvements](#-future-improvements)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✦ Why This Project Is Different

Most LLM-powered applications pass a user query directly to a single model and return the response. OmniMind AI is architected differently — the query passes through a **stateful, observable, multi-agent pipeline** where each stage has a distinct cognitive responsibility.

| Dimension | Typical LLM App | OmniMind AI |
|---|---|---|
| Response generation | Single LLM call | Three specialized agents in sequence |
| Reasoning visibility | Opaque | Live pipeline visualization via WebSocket |
| Knowledge source | LLM parameters only | LLM + RAG retrieval + live web search |
| Response latency UX | Wait for full response | Word-by-word streaming with typing cursor |
| Mathematical queries | LLM reasoning (error-prone) | SymPy CAS solver — exact, deterministic |
| State persistence | Session-only | PostgreSQL-backed conversation history |
| Deployment | Script-based | Fully containerized via Docker Compose |

The system exposes its internal reasoning pipeline as a first-class UI element: users see the Planner, Research, and Critic agents activate sequentially with GSAP-animated status updates driven by WebSocket events. This makes AI behavior auditable, not just functional.

---

## ✦ Key Engineering Challenges Solved

### 1. Streaming UX Without Server-Sent Events
Rather than blocking until the entire LLM response is generated, the system returns the full response payload immediately and the React frontend performs word-by-word rendering at ~40 words/second using `setInterval`. This eliminates backend streaming infrastructure complexity while preserving the low-latency typing UX.

### 2. Agent Coordination Without Race Conditions
LangGraph's `StateGraph` enforces a strict directed acyclic execution order. Each node receives an immutable copy of `AgentState`, modifies exactly one field, and returns the updated dict. This prevents state mutations from one agent affecting another mid-execution, a common failure mode in naive multi-agent systems.

### 3. Intelligent Query Routing Before LLM Invocation
A `router_node` at the graph entry point intercepts queries that can be resolved deterministically — date lookups and mathematical expressions — and short-circuits the entire LLM pipeline. This reduces token consumption and average response latency significantly for a large class of queries.

### 4. Safe Mathematical Expression Evaluation
Python's `eval()` is used with a fully restricted globals dict (`__builtins__: {}`) and a symbol whitelist. Attribute access patterns that would enable sandbox escapes (e.g. `().__class__.__bases__`) are blocked by a pre-evaluation regex check. SymPy handles algebraic systems where `eval()` is insufficient.

### 5. Async Pipeline Without Blocking the Event Loop
FastAPI's async request handler calls `await compiled_graph.ainvoke(state)` which propagates async execution through the entire LangGraph pipeline. Synchronous operations (Chroma retrieval, DuckDuckGo fallback) are isolated and do not block the Uvicorn event loop due to their placement in non-async tool functions called from async node wrappers.

### 6. State Persistence Across Sessions
Chat history is persisted to PostgreSQL after every message addition. The frontend additionally maintains a `localStorage` cache so the UI rehydrates immediately on page load without waiting for a network round-trip.

---

## ✦ Features

### Core AI Capabilities
- **Multi-Agent Pipeline** — Planner, Research, and Critic agents collaborate sequentially via LangGraph orchestration
- **Retrieval Augmented Generation (RAG)** — HuggingFace sentence embeddings + Chroma vector store for semantic document retrieval
- **Live Web Search** — Tavily Search API integration for real-time query grounding
- **Intelligent Router** — Pre-LLM routing for date queries, arithmetic expressions, and algebraic equation systems
- **SymPy Equation Solver** — Exact algebraic solutions for systems of equations without LLM involvement
- **Streaming Responses** — Word-by-word response rendering with animated typing cursor

### Engineering Infrastructure
- **WebSocket Agent Updates** — Real-time agent status events pushed over `ws://host/ws/agents`
- **Live Pipeline Visualization** — GSAP-animated agent cards reflecting Planner → Research → Critic execution state
- **Document Ingestion** — PDF and TXT upload endpoint with chunk-based vector store ingestion
- **Persistent Chat History** — Full conversation persistence with localStorage caching and PostgreSQL backend
- **Centralized Logging** — Structured `logging` hierarchy (`app.*`) with consistent `[timestamp][level][module]` format
- **Custom Exception Hierarchy** — `AppException → ToolException | AgentException` with FastAPI global handlers
- **Docker Compose Deployment** — Single-command environment bootstrap for backend, frontend, PostgreSQL, and Redis

### Frontend UX
- **Animated Agent Panel** — Real-time per-agent status: `idle → thinking → active → done` with GSAP glow and float effects
- **Tool Badges** — Contextual detection of web search, RAG retrieval, calculator, and date tool usage displayed inline
- **Auto-titled Chat History** — First message auto-generates a chat title; full history persisted in sidebar
- **Responsive Input** — Auto-expanding textarea with `Enter`-to-send, `Shift+Enter`-for-newline

---

## ✦ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           OmniMind AI System                            │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                     React Frontend (Vite)                         │  │
│  │   Sidebar │ ChatWindow │ AgentPanel │ PipelineStrip │ ToolBadges  │  │
│  │           │            │            │               │             │  │
│  │   useChat │ useAgents  │ useStreamer │ parseResponse │ useChatHist │  │
│  └─────────────────────────────┬─────────────────┬─────────────────-┘  │
│                                │ HTTP REST        │ WebSocket           │
│                                │ POST /api/v1/ask │ ws://host/ws/agents │
│  ┌─────────────────────────────▼─────────────────▼────────────────-─┐  │
│  │                    FastAPI Application Server                      │  │
│  │                                                                   │  │
│  │  ┌────────────┐   ┌───────────────┐   ┌───────────────────────┐  │  │
│  │  │ api/routes │   │ Exception     │   │  WebSocket Manager    │  │  │
│  │  │ schemas    │   │ Handlers      │   │  /ws/agents           │  │  │
│  │  └─────┬──────┘   └───────────────┘   └───────────────────────┘  │  │
│  │        │                                                           │  │
│  │  ┌─────▼──────────────────────────────────────────────────────┐  │  │
│  │  │                 agent_service.py                            │  │  │
│  │  │              run_agent_pipeline(query)                      │  │  │
│  │  └─────┬──────────────────────────────────────────────────────┘  │  │
│  │        │                                                           │  │
│  │  ┌─────▼──────────────────────────────────────────────────────┐  │  │
│  │  │              LangGraph StateGraph (compiled)                │  │  │
│  │  │                                                             │  │  │
│  │  │  START → router_node → [conditional edge]                  │  │  │
│  │  │                              │                              │  │  │
│  │  │            ┌─────────────────┴──────────────────┐          │  │  │
│  │  │            │ final_answer set?                   │          │  │  │
│  │  │            │ YES → END        NO → planner_node  │          │  │  │
│  │  │            └─────────────────┬──────────────────┘          │  │  │
│  │  │                              │                              │  │  │
│  │  │                    research_node                            │  │  │
│  │  │                              │                              │  │  │
│  │  │                     critic_node → [retry or END]           │  │  │
│  │  └─────────────────────────────────────────────────────────── ┘  │  │
│  └────────────────────────────────────────────────────────────────── ┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     External Services                            │   │
│  │                                                                  │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │   │
│  │  │  Groq    │  │  Tavily  │  │  Chroma  │  │  PostgreSQL    │  │   │
│  │  │ LLaMA3   │  │  Search  │  │  Vector  │  │  Conversations │  │   │
│  │  │  (LLM)   │  │   API    │  │  Store   │  │  & Messages    │  │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## ✦ Multi-Agent Workflow

The system implements a **Plan → Research → Critique** cognitive architecture inspired by how expert teams solve complex problems. Each agent is a distinct LangGraph node with a defined input slice, output slice, and prompt contract.

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                       router_node                           │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Intent Classification                               │  │
│  │                                                      │  │
│  │  DATE query?  ──────────────────► get_current_date() │  │
│  │  MATH expr?   ──────────────────► calculate()        │  │
│  │  EQUATION sys?──────────────────► solve_equations()  │  │
│  │  UNKNOWN      ──────────────────► continue pipeline  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
    │ (if not short-circuited)
    ▼
┌─────────────────────────────────────────────────────────────┐
│                      planner_node                           │
│                                                             │
│  PlannerAgent: "Break the query into step-by-step           │
│  reasoning" → writes AgentState["plan"]                     │
│                                                             │
│  Output: Structured reasoning decomposition                 │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                      research_node                          │
│                                                             │
│  ResearchAgent:                                             │
│                                                             │
│  ┌──────────────────┐    ┌──────────────────────────────┐  │
│  │  REALTIME query? │    │  KNOWLEDGE query?             │  │
│  │                  │    │                               │  │
│  │  → web_search()  │    │  → retriever_tool()           │  │
│  │  → [Web Search]  │    │  → [Knowledge Base]           │  │
│  │  context block   │    │  context block                │  │
│  └────────┬─────────┘    └───────────────┬───────────── ┘  │
│           └────────────────┬─────────────┘                  │
│                            ▼                                 │
│              LLM synthesis with forcing prompt              │
│              → writes AgentState["answer"]                  │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                       critic_node                           │
│                                                             │
│  CriticAgent: "Evaluate the answer. If it can be           │
│  improved, provide a better version."                       │
│                                                             │
│  → writes AgentState["final_answer"]                        │
│                                                             │
│  Conditional edge:                                          │
│    final_answer non-empty → END                             │
│    final_answer empty     → retry research_node             │
└─────────────────────────────────────────────────────────────┘
    │
    ▼
  Response returned to client
```

### AgentState Schema

```python
class AgentState(TypedDict):
    user_query:   str   # Original user input — read by all nodes
    plan:         str   # Written by planner_node
    answer:       str   # Written by research_node
    final_answer: str   # Written by critic_node or router_node
```

Each node performs an **immutable state update** — it receives the full state, modifies one field, and returns `{**state, "key": new_value}`. This ensures LangGraph's checkpoint system can replay any node from a saved state snapshot.

---

## ✦ GenAI Concepts Used

### Prompt Engineering
Each agent operates under a carefully designed prompt contract:

- **PlannerAgent** uses a decomposition prompt that constrains the LLM to produce step-by-step reasoning rather than a direct answer. This prevents premature conclusion-jumping.
- **ResearchAgent** uses a **forcing prompt** with imperative language ("You MUST base your answer on the Web Results below. Do NOT rely on your training knowledge") to override the LLM's default preference for parametric knowledge on recency-sensitive queries.
- **CriticAgent** uses a conditional improvement prompt: it either returns the original answer unchanged or provides a corrected version — avoiding the common problem of critique agents that always produce verbose rewrites.

### Context Window Management
Retrieved context is assembled in priority order:

```
[Web Search]       ← freshest, highest priority (top 5 Tavily snippets)
[Knowledge Base]   ← curated internal documents (top 4 Chroma chunks)
```

Web content is placed first to exploit the LLM's recency bias in long contexts. Each source is labelled with a section header so the LLM can distinguish and attribute them independently.

### Temperature & Model Configuration
The system uses `llama3-70b-8192` via Groq's inference API. A single `get_llm()` function returns a configured `ChatGroq` instance that is passed to agents at instantiation time — ensuring consistent model parameters across the entire pipeline without redundant initialization.

---

## ✦ RAG Pipeline

Retrieval Augmented Generation grounds LLM responses in private or real-time knowledge that the base model was not trained on.

```
Document Ingestion                    Query Time
──────────────────                    ──────────
                                      
User uploads PDF/TXT                  User submits query
        │                                    │
        ▼                                    ▼
RecursiveCharacterTextSplitter        HuggingFaceEmbeddings
chunk_size=512, overlap=64            (all-MiniLM-L6-v2)
        │                                    │
        ▼                                    ▼
HuggingFaceEmbeddings                 Query vector (384-dim)
(all-MiniLM-L6-v2)                           │
        │                                    ▼
        ▼                             Chroma similarity_search(k=4)
Chroma vector store                          │
(persisted to ./chroma_db)                   ▼
                                      Top-4 document chunks
                                             │
                                             ▼
                                      Injected into ResearchAgent
                                      context as [Knowledge Base]
```

**Embedding Model**: `sentence-transformers/all-MiniLM-L6-v2` produces 384-dimensional dense vectors that capture semantic meaning beyond keyword overlap. A query about "vehicle fuel efficiency" will retrieve documents containing "car miles per gallon" even without exact term matches.

**Chunking Strategy**: `RecursiveCharacterTextSplitter` with 512-token chunks and 64-token overlap ensures that sentence boundaries are preserved across chunk edges, preventing semantic fragmentation.

**Vector Store**: Chroma persists index data to disk at `./chroma_db`, allowing the retrieval index to survive server restarts without re-ingestion.

---

## ✦ WebSocket & Streaming Architecture

### WebSocket Agent Updates

The system pushes real-time agent status events to the frontend over a persistent WebSocket connection, enabling live pipeline visualization without polling.

```
Backend (FastAPI)                Frontend (React)
─────────────────                ────────────────

ws://host/ws/agents ←──────────── useAgents hook
                                  (connects on mount)
        │
        │ On pipeline execution:
        │
        ├─ send: {"agent": "planner",  "status": "thinking"}
        ├─ send: {"agent": "planner",  "status": "active"}
        ├─ send: {"agent": "planner",  "status": "done"}
        ├─ send: {"agent": "research", "status": "thinking"}
        │  ...
        └─ send: {"agent": "critic",   "status": "done"}
                                  │
                                  ▼
                            setAgentStates(prev => ({
                              ...prev, [agent]: status
                            }))
                                  │
                                  ▼
                            GSAP animation
                            triggered per card
```

**Graceful Degradation**: The WebSocket connection is wrapped in a `try/catch`. If the backend WebSocket endpoint is unavailable, the frontend falls back to a local timer-based animation that approximates the expected pipeline duration. The user experience degrades gracefully with no visible errors.

### Response Streaming

```
Backend returns full response payload (single HTTP response)
        │
        ▼
parseResponse() strips plan, returns clean answer string
        │
        ▼
useStreamer.stream(fullText)
        │
        ▼
setInterval at 28ms (~35 words/second)
        │
        ├── words.slice(0, idx).join(" ")
        ├── setState → re-render Bubble component
        ├── auto-scroll via bottomRef
        └── animated typing cursor (CSS blink keyframe)
        │
        ▼ (when idx >= words.length)
clearInterval → setStreaming(false) → cursor disappears
```

This approach trades true token-level streaming (which would require SSE or WebSocket streaming from the LLM provider) for implementation simplicity, while preserving the full streaming UX benefit of progressive content reveal.

---

## ✦ Backend Architecture

```
backend/
├── app/
│   ├── main.py                  # FastAPI app, CORS, exception handlers
│   ├── api/
│   │   ├── routes.py            # POST /ask, GET /debug/websearch, POST /upload
│   │   └── schemas.py           # Pydantic request/response models
│   ├── core/
│   │   ├── config.py            # Pydantic BaseSettings, absolute .env path
│   │   └── llm.py               # ChatGroq factory function
│   ├── agents/
│   │   ├── base_agent.py        # ABC with abstract async run()
│   │   ├── planner_agent.py     # Reasoning decomposition
│   │   ├── research_agent.py    # RAG + web search + routing
│   │   └── critic_agent.py      # Answer evaluation and improvement
│   ├── graph/
│   │   ├── nodes.py             # LangGraph node functions
│   │   ├── graph_builder.py     # StateGraph assembly and compilation
│   │   └── executor.py          # run_graph() entry point
│   ├── rag/
│   │   ├── vectorstore.py       # Chroma + HuggingFace embeddings
│   │   ├── ingest.py            # Text chunking and indexing
│   │   └── retriever.py         # similarity_search wrapper
│   ├── tools/
│   │   ├── tool_registry.py     # Centralized tool registration
│   │   ├── web_search.py        # Tavily API integration
│   │   ├── retriever_tool.py    # RAG tool wrapper
│   │   └── system_tools.py      # get_current_date, calculate, solve_equations
│   ├── models/
│   │   └── state_model.py       # AgentState TypedDict
│   ├── services/
│   │   └── agent_service.py     # Pipeline orchestration entry point
│   ├── utils/
│   │   ├── logger.py            # Centralized logging configuration
│   │   └── prompt_templates.py  # All prompt strings (single source of truth)
│   └── exceptions/
│       ├── custom_exceptions.py # AppException, ToolException, AgentException
│       └── handlers.py          # FastAPI global exception handlers
└── requirements.txt
```

### Design Principles

**Dependency direction**: `api → services → graph → agents → tools`. No circular imports. The API layer never imports agent classes directly.

**Singleton pattern**: `get_llm()`, `get_settings()`, `get_embeddings()`, and `compiled_graph` are all module-level singletons. Expensive objects (model loading, graph compilation) are constructed once per process lifetime.

**Absolute imports only**: All internal imports use `from app.module.submodule import name` — relative imports are prohibited to prevent path resolution issues across deployment environments.

---

## ✦ Frontend Architecture

```
src/
├── hooks/
│   ├── useChat.js           # localStorage + in-memory chat state
│   ├── useAgents.js         # WebSocket connection + agent state machine
│   └── useStreamer.js       # Word-by-word text streaming
├── components/
│   ├── Sidebar.jsx          # Chat history, new chat, document upload
│   ├── ChatWindow.jsx       # Messages, pipeline strip, input
│   ├── AgentPanel.jsx       # GSAP-animated agent cards
│   ├── PipelineStrip.jsx    # Planner→Research→Critic progress bar
│   └── ToolBadges.jsx       # Inline tool usage indicators
├── utils/
│   └── parseResponse.js     # Response parsing and tool detection
└── pages/
    └── Home.jsx             # Root orchestrator — wires all hooks + components
```

### State Architecture

```
Home.jsx (orchestrator)
│
├── useChat()          → { chats, activeChat, addMessage, updateMessage }
├── useAgents()        → { agentStates, pipelineStage, runPipeline }
├── useStreamer()       → { text, streaming, stream }
│
├── Props to Sidebar:  chats, activeChatId, handlers
├── Props to ChatWindow: messages, pipelineStage, loading, streamingMsgId
└── Props to AgentPanel: agentStates, pipelineStage
```

State flows unidirectionally downward. All mutation callbacks originate in `Home.jsx` and are passed as props. No component holds business state that another component needs to read — eliminating prop-drilling workarounds and context complexity.

---

## ✦ Database Design

PostgreSQL stores conversation history with a normalized schema that supports multiple users and long session histories.

```sql
-- Conversations table
CREATE TABLE conversations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     VARCHAR(255) NOT NULL,
    title       VARCHAR(500),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Messages table
CREATE TABLE messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    tool_metadata   JSONB,          -- stores detected tool badges
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for common query patterns
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC);
```

**JSONB `tool_metadata`**: Stores structured tool usage data (e.g., `{"tools": ["web_search", "rag"], "query": "..."}`) alongside each assistant message. This enables future analytics on tool usage patterns without schema migrations.

**`ON DELETE CASCADE`**: Deleting a conversation automatically removes all associated messages, maintaining referential integrity without application-level cleanup logic.

---

## ✦ Docker & DevOps

The entire system is containerized with Docker Compose for consistent, reproducible deployment across development, staging, and production environments.

```yaml
# docker-compose.yml (abbreviated)
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres, redis]
    volumes:
      - ./chroma_db:/app/chroma_db  # Persist vector store

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: omnimind
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

**Environment isolation**: Each service has access only to the environment variables it needs. The backend receives `GROQ_API_KEY`, `TAVILY_API_KEY`, and database credentials; the frontend receives only `VITE_API_URL`.

**Volume persistence**: Both PostgreSQL and Redis data are mounted to named Docker volumes, surviving container restarts and rebuilds. The Chroma vector store is mounted as a bind mount so ingested documents persist across backend container recreation.

**Health checks**: Production deployments should add `healthcheck` directives to `postgres` and `redis` services so the backend container waits for dependency readiness before accepting traffic.

---

## ✦ Scalability Considerations

### Horizontal Scaling

FastAPI runs on Uvicorn with a single worker by default. For production, run behind Gunicorn with multiple Uvicorn workers:

```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

The `compiled_graph` singleton is created per-process (not per-request), so graph compilation overhead is amortized across all requests within a worker process.

### Celery + Redis Task Queue

Long-running agent pipeline executions can be offloaded to Celery workers, freeing the API layer to return a task ID immediately and allowing the client to poll or receive WebSocket updates on completion:

```python
# Future: celery/tasks.py
@celery_app.task
def run_pipeline_task(query: str, chat_id: str) -> str:
    result = asyncio.run(run_agent_pipeline(query))
    # Push result to Redis pub/sub → WebSocket → frontend
    return result
```

This decouples request handling from pipeline execution, enabling the system to handle more concurrent users than the number of available LLM API connections.

### Vector Store Scaling

The current Chroma local deployment is suitable for development and small production workloads (< 1M vectors). For larger deployments, migrate to:

- **Pinecone** or **Weaviate** for managed, distributed vector search
- **pgvector** PostgreSQL extension to colocate vector and relational data
- **Qdrant** for self-hosted, high-throughput vector search with filtering

### LLM API Rate Limits

Groq's LPU inference provides exceptional throughput, but production deployments should implement:

- **Request queuing** via Redis to smooth burst traffic
- **Circuit breaker** pattern to fail fast when Groq is unavailable
- **Response caching** for identical queries within a time window

---

## ✦ Security Considerations

| Layer | Measure |
|---|---|
| API Keys | Loaded via Pydantic `BaseSettings` from `.env`; never hardcoded or logged beyond first 10 characters |
| `eval()` sandbox | `__builtins__: {}` + whitelist + attribute-access regex block |
| CORS | Configured at FastAPI middleware level; restrict `allow_origins` in production |
| Input validation | Pydantic models enforce type and length constraints on all API inputs |
| SQL injection | Use parameterized queries / ORM (SQLAlchemy) exclusively |
| File uploads | Validate MIME type and extension server-side; scan with ClamAV in production |
| WebSocket auth | Add JWT validation on WebSocket handshake for production deployments |
| Secrets in containers | Use Docker secrets or a secrets manager (Vault, AWS Secrets Manager) instead of `.env` files in production |
| Dependency scanning | Run `pip-audit` and `npm audit` in CI pipeline before deployment |

---

## ✦ Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Runtime |
| FastAPI | 0.110+ | Async HTTP API framework |
| LangGraph | 0.1+ | Stateful multi-agent orchestration |
| LangChain | 0.2+ | LLM abstraction and tool integration |
| LangChain-Groq | latest | Groq LPU inference integration |
| LangChain-Chroma | latest | Vector store integration |
| LangChain-HuggingFace | latest | Sentence embedding models |
| Uvicorn | latest | ASGI server |
| Pydantic v2 | latest | Data validation and settings |
| SymPy | latest | Computer algebra system |
| Tavily Python | latest | Web search API client |
| PostgreSQL | 16 | Conversation persistence |
| Redis | 7 | Cache and Celery broker |
| Celery | 5+ | Async task queue |
| Docker | 24+ | Containerization |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18+ | UI framework |
| Vite | 5+ | Build tool |
| Tailwind CSS | 3+ | Utility-first styling |
| GSAP | 3+ | High-performance animations |
| Axios | 1+ | HTTP client |

### AI / ML
| Technology | Purpose |
|---|---|
| Groq LPU | Ultra-low-latency LLM inference |
| LLaMA3-70b | Primary reasoning model |
| all-MiniLM-L6-v2 | 384-dim sentence embeddings for RAG |
| Tavily Search API | Real-time web retrieval |
| Chroma | Local vector database |
| SymPy CAS | Exact algebraic computation |

---

## ✦ API Endpoints

### REST API

| Method | Endpoint | Description | Request Body | Response |
|---|---|---|---|---|
| `POST` | `/api/v1/ask` | Run multi-agent pipeline | `{"query": "string"}` | `{"response": "string"}` |
| `POST` | `/api/v1/upload` | Ingest document into RAG | `multipart/form-data (file)` | `{"status": "ok", "filename": "..."}` |
| `GET` | `/api/v1/debug/websearch` | Test web search tool | `?q=query_string` | `{"query": "...", "count": N, "results": [...]}` |
| `GET` | `/health` | Health check | — | `{"status": "ok"}` |

### WebSocket

| Endpoint | Direction | Event Schema |
|---|---|---|
| `ws://host/ws/agents` | Server → Client | `{"agent": "planner\|research\|critic", "status": "idle\|thinking\|active\|done"}` |

### Example Request/Response

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest developments in AI safety research?"}'
```

```json
{
  "response": "Recent AI safety research has focused on three primary areas: interpretability, alignment, and robustness...\n\n[substantive answer based on Tavily web search results]"
}
```

---

## ✦ Project Structure

```
omnimind-ai/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── routes.py
│   │   │   └── schemas.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── llm.py
│   │   ├── agents/
│   │   │   ├── base_agent.py
│   │   │   ├── planner_agent.py
│   │   │   ├── research_agent.py
│   │   │   └── critic_agent.py
│   │   ├── graph/
│   │   │   ├── nodes.py
│   │   │   ├── graph_builder.py
│   │   │   └── executor.py
│   │   ├── rag/
│   │   │   ├── vectorstore.py
│   │   │   ├── ingest.py
│   │   │   └── retriever.py
│   │   ├── tools/
│   │   │   ├── tool_registry.py
│   │   │   ├── web_search.py
│   │   │   ├── retriever_tool.py
│   │   │   └── system_tools.py
│   │   ├── models/
│   │   │   └── state_model.py
│   │   ├── services/
│   │   │   └── agent_service.py
│   │   ├── utils/
│   │   │   ├── logger.py
│   │   │   └── prompt_templates.py
│   │   └── exceptions/
│   │       ├── custom_exceptions.py
│   │       └── handlers.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useChat.js
│   │   │   ├── useAgents.js
│   │   │   └── useStreamer.js
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   ├── ChatWindow.jsx
│   │   │   ├── AgentPanel.jsx
│   │   │   ├── PipelineStrip.jsx
│   │   │   └── ToolBadges.jsx
│   │   ├── utils/
│   │   │   └── parseResponse.js
│   │   └── pages/
│   │       └── Home.jsx
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## ✦ Installation

### Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose (for containerized deployment)
- API Keys: [Groq](https://console.groq.com) · [Tavily](https://app.tavily.com)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/omnimind-ai.git
cd omnimind-ai
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
# LLM
GROQ_API_KEY=gsk_your_groq_api_key_here
MODEL_NAME=llama3-70b-8192

# Web Search
TAVILY_API_KEY=tvly-your_tavily_key_here

# Database
POSTGRES_USER=omnimind
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=omnimind
DATABASE_URL=postgresql://omnimind:your_secure_password@postgres:5432/omnimind

# Redis
REDIS_URL=redis://redis:6379/0
```

---

## ✦ Running Locally

### Option A — Docker Compose (Recommended)

```bash
docker compose up --build
```

Services will be available at:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

### Option B — Manual Development Setup

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

**Verify the pipeline:**

```bash
# Health check
curl http://localhost:8000/health

# Test a query
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain the concept of transformer attention"}'

# Test web search
curl "http://localhost:8000/api/v1/debug/websearch?q=latest+AI+news"
```

### Option C — Production Deployment

```bash
# Build production images
docker compose -f docker-compose.prod.yml build

# Run with resource limits
docker compose -f docker-compose.prod.yml up -d

# View logs
docker compose logs -f backend
```

---

## ✦ Screenshots

> Screenshots and demo videos will be added following the first public release.

| View | Description |
|---|---|
| `screenshots/01-welcome.png` | Welcome screen with suggestion chips |
| `screenshots/02-pipeline.png` | Live pipeline visualization during query |
| `screenshots/03-agents-active.png` | Agent cards in active/thinking states |
| `screenshots/04-response.png` | Streamed response with tool badges |
| `screenshots/05-chat-history.png` | Sidebar with auto-titled conversation history |
| `screenshots/06-math-solver.png` | Equation system solved without LLM |
| `screenshots/07-rag-upload.png` | Document upload and RAG ingestion |

---

## ✦ Future Improvements

### Near-Term
- [ ] **True token streaming** — SSE endpoint that streams LLM tokens as they are generated by Groq's API, replacing the word-interval simulation
- [ ] **User authentication** — JWT-based auth with per-user conversation isolation
- [ ] **PostgreSQL persistence** — Complete ORM layer (SQLAlchemy + Alembic migrations) replacing localStorage
- [ ] **WebSocket agent status** — Backend emitting real status events synchronized with actual LangGraph node execution
- [ ] **Conversation branching** — Allow users to fork a conversation from any message
- [ ] **Message editing** — Edit a previous user message and regenerate from that point

### Medium-Term
- [ ] **Multi-modal input** — Accept image uploads for vision-capable model endpoints
- [ ] **Agent memory** — LangGraph `MemorySaver` checkpoint integration for conversation-aware responses
- [ ] **Pluggable agent registry** — Add new agents without modifying `graph_builder.py` via a decorator-based registration system
- [ ] **Evaluation harness** — Automated pipeline for measuring response quality across a test query set
- [ ] **OpenAI / Anthropic** model backends as drop-in alternatives to Groq

### Long-Term
- [ ] **Kubernetes deployment** — Helm chart for production-grade orchestration with HPA and pod disruption budgets
- [ ] **Distributed vector search** — Migration from local Chroma to Pinecone or Weaviate for multi-tenant workloads
- [ ] **Real-time collaboration** — Multiple users in the same conversation session via CRDT-based shared state
- [ ] **Agent marketplace** — User-definable custom agents loaded from configuration files

---

## ✦ Contributing

Contributions are welcome. Please follow these guidelines to keep the codebase consistent.

### Development Workflow

```bash
# 1. Fork and clone
git clone https://github.com/yourusername/omnimind-ai.git

# 2. Create a feature branch
git checkout -b feat/your-feature-name

# 3. Make changes, write tests
# Backend: pytest backend/tests/
# Frontend: npm test

# 4. Commit with conventional commits
git commit -m "feat(agents): add summarizer agent node"
git commit -m "fix(router): prevent false math detection on hyphenated words"
git commit -m "docs(readme): add WebSocket architecture section"

# 5. Push and open a pull request
git push origin feat/your-feature-name
```

### Code Standards

**Backend:**
- Absolute imports only (`from app.module import ...`)
- Type hints on every function signature
- Docstrings on all public functions and classes
- New agents must extend `BaseAgent` and implement `async def run(self, input_text: str) -> str`
- All exceptions must be `AppException` subclasses

**Frontend:**
- Functional components with hooks only (no class components)
- Business logic in hooks, not in JSX files
- GSAP animations via `ref` + `useEffect` — never inline styles that conflict with GSAP tweens
- Tailwind for all styling — no separate CSS files

### Pull Request Checklist

- [ ] Code follows the style and architecture conventions above
- [ ] No new `print()` statements — use `logger` from `app.utils.logger`
- [ ] New environment variables are added to `.env.example` and `app/core/config.py`
- [ ] New API endpoints are documented in this README
- [ ] Docker Compose still builds and runs cleanly after changes

---

## ✦ License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

Built with precision and care — modular by design, observable by default.

⬡ **OmniMind AI** — Where intelligence is a pipeline, not a black box.

</div>