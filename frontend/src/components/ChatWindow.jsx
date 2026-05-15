// ChatWindow.jsx — streaming, plan visualization, tool badges, all bugs fixed
import { useState, useRef, useEffect, useCallback } from "react";
import { gsap } from "gsap";
import { AGENTS } from "../hooks/useAgents";
import { detectTools } from "../utils/parseResponse";

// ── Pipeline Strip ──────────────────────────────────────────────────────────
function PipelineStrip({ pipelineStage, visible }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    if (visible) {
      gsap.fromTo(ref.current, { opacity: 0, y: -6 }, { opacity: 1, y: 0, duration: 0.28, ease: "power2.out" });
    } else {
      gsap.to(ref.current, { opacity: 0, y: -4, duration: 0.2 });
    }
  }, [visible]);

  const stageIdx = AGENTS.findIndex(a => a.id === pipelineStage);

  return (
    <div
      ref={ref}
      className="mx-4 mt-4 rounded-2xl px-4 py-2.5 flex items-center gap-2 shrink-0"
      style={{
        backgroundColor: "#141417",
        border: "1px solid #27272a",
        opacity: 0,
        display: visible ? "flex" : "none",
      }}
    >
      <span className="text-xs mr-1" style={{ color: "#52525b" }}>Running:</span>
      {AGENTS.map((agent, i) => {
        const isDone   = pipelineStage === "done" || i < stageIdx;
        const isActive = i === stageIdx && pipelineStage !== "done";
        return (
          <div key={agent.id} className="flex items-center gap-1.5">
            <span
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor: isDone ? "#22c55e" : isActive ? agent.accent : "#27272a",
                boxShadow: isActive ? `0 0 6px ${agent.accent}` : "none",
                transition: "all 0.3s",
              }}
            />
            <span className="text-xs" style={{ color: isDone ? "#22c55e" : isActive ? agent.accent : "#3f3f46", transition: "color 0.3s" }}>
              {agent.label}
            </span>
            {i < AGENTS.length - 1 && (
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" style={{ color: "#27272a", marginLeft: 2 }}>
                <path d="M2 5H8M8 5L5 2M8 5L5 8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Tool Badges ─────────────────────────────────────────────────────────────
function ToolBadges({ content }) {
  const tools = detectTools(content);
  if (!tools.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mb-1.5">
      {tools.map(t => (
        <span
          key={t.key}
          className="flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs"
          style={{ backgroundColor: "#1a1a1d", border: "1px solid #27272a", color: "#71717a" }}
        >
          {t.icon} {t.label}
        </span>
      ))}
    </div>
  );
}

// ── Typing Indicator ────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex gap-3">
      <Avatar isAi />
      <div
        className="flex items-center gap-1.5 rounded-2xl px-4 py-3"
        style={{ backgroundColor: "#1a1a1d", border: "1px solid #27272a" }}
      >
        {[0, 1, 2].map(i => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full"
            style={{ backgroundColor: "#8b5cf6", animation: `omni-dot 1.2s ease-in-out ${i * 0.2}s infinite` }}
          />
        ))}
      </div>
    </div>
  );
}

// ── Avatar ──────────────────────────────────────────────────────────────────
function Avatar({ isAi }) {
  return (
    <div
      className="w-7 h-7 rounded-full shrink-0 flex items-center justify-center text-xs font-bold mt-1"
      style={{
        backgroundColor: isAi ? "#1a1a1d" : "#8b5cf6",
        border: isAi ? "1px solid #27272a" : "none",
        color: isAi ? "#8b5cf6" : "#fff",
      }}
    >
      {isAi ? (
        <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
          <path d="M8 2L13 5V11L8 14L3 11V5L8 2Z" stroke="#8b5cf6" strokeWidth="1.5" strokeLinejoin="round" />
          <circle cx="8" cy="8" r="2" fill="#8b5cf6" />
        </svg>
      ) : "U"}
    </div>
  );
}

// ── Message Bubble ──────────────────────────────────────────────────────────
function Bubble({ message, streamText, isStreamingThis }) {
  const ref = useRef(null);
  const isUser = message.role === "user";
  const content = isStreamingThis ? streamText : message.content;

  useEffect(() => {
    if (!ref.current) return;
    gsap.fromTo(ref.current,
      { opacity: 0, y: 12, scale: 0.97 },
      { opacity: 1, y: 0, scale: 1, duration: 0.3, ease: "power2.out" }
    );
  }, []);

  return (
    <div ref={ref} className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <Avatar isAi={!isUser} />
      <div className={`flex flex-col max-w-md ${isUser ? "items-end" : "items-start"}`}>
        {!isUser && <ToolBadges content={message.content} />}
        <div
          className="rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap"
          style={{
            backgroundColor: isUser ? "#8b5cf6" : "#1a1a1d",
            border: isUser ? "none" : "1px solid #27272a",
            color: isUser ? "#fff" : "#d4d4d8",
          }}
        >
          {content || <span style={{ color: "#3f3f46" }}>…</span>}
          {isStreamingThis && (
            <span
              className="inline-block w-0.5 h-4 ml-0.5 align-middle rounded-full"
              style={{ backgroundColor: "#8b5cf6", animation: "omni-blink 0.85s step-end infinite" }}
            />
          )}
        </div>
      </div>
    </div>
  );
}

// ── Suggestions ─────────────────────────────────────────────────────────────
const SUGGESTIONS = [
  { icon: "🔍", text: "Latest AI research breakthroughs" },
  { icon: "🧮", text: "Solve: a+b=10 and a-b=8" },
  { icon: "📅", text: "What is today's date?" },
  { icon: "📊", text: "Plan a Q2 product launch strategy" },
];

// ── Main ChatWindow ─────────────────────────────────────────────────────────
export default function ChatWindow({ messages, pipelineStage, loading, streamingMsgId, streamText, onSend }) {
  const [input, setInput] = useState("");
  const bottomRef    = useRef(null);
  const inputRef     = useRef(null);
  const inputWrapRef = useRef(null);
  const sendBtnRef   = useRef(null);

  const isEmpty = messages.length === 0 && !loading;

  // Auto-scroll on new content
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamText, loading]);

  const send = useCallback((text) => {
    const q = (text ?? input).trim();
    if (!q || loading) return;
    setInput("");
    if (inputRef.current) inputRef.current.style.height = "auto";
    // Send-button micro-animation
    if (sendBtnRef.current) {
      gsap.to(sendBtnRef.current, {
        scale: 0.87, duration: 0.08,
        onComplete: () => gsap.to(sendBtnRef.current, { scale: 1, duration: 0.2, ease: "back.out(2.5)" }),
      });
    }
    onSend(q);
  }, [input, loading, onSend]);

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  };

  const handleFocus = () => gsap.to(inputWrapRef.current, { boxShadow: "0 0 0 2px rgba(139,92,246,0.3)", duration: 0.2 });
  const handleBlur  = () => gsap.to(inputWrapRef.current, { boxShadow: "none", duration: 0.2 });

  return (
    <main className="flex-1 flex flex-col h-full min-w-0" style={{ backgroundColor: "#0f0f11" }}>
      {/* Global keyframes */}
      <style>{`
        @keyframes omni-blink { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes omni-dot   { 0%,100%{transform:translateY(0);opacity:.35} 50%{transform:translateY(-5px);opacity:1} }
      `}</style>

      {/* Top bar */}
      <div className="flex items-center justify-between px-6 py-4 border-b shrink-0" style={{ borderColor: "#27272a" }}>
        <div className="flex items-center gap-2">
          <span
            className="w-2 h-2 rounded-full"
            style={{
              backgroundColor: loading ? "#f59e0b" : "#22c55e",
              boxShadow: `0 0 6px ${loading ? "#f59e0b" : "#22c55e"}`,
              transition: "background-color 0.3s",
            }}
          />
          <span className="text-xs" style={{ color: "#71717a" }}>
            {loading ? "Pipeline running…" : "Pipeline ready"}
          </span>
        </div>
        <span className="text-xs" style={{ color: "#3f3f46" }}>Planner → Research → Critic</span>
      </div>

      {/* Pipeline strip */}
      <PipelineStrip pipelineStage={pipelineStage} visible={!!pipelineStage} />

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        {isEmpty ? (
          /* ── Welcome ── */
          <div className="flex flex-col items-center justify-center h-full gap-8">
            <div className="text-center">
              <div
                className="w-14 h-14 rounded-2xl mx-auto mb-5 flex items-center justify-center"
                style={{ background: "linear-gradient(135deg,#8b5cf6,#6d28d9)", boxShadow: "0 0 40px rgba(139,92,246,0.3)" }}
              >
                <svg width="26" height="26" viewBox="0 0 16 16" fill="none">
                  <path d="M8 2L13 5V11L8 14L3 11V5L8 2Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round" />
                  <circle cx="8" cy="8" r="2" fill="white" />
                </svg>
              </div>
              <h1 className="text-xl font-semibold mb-1.5" style={{ color: "#f4f4f5" }}>OmniMind AI</h1>
              <p className="text-sm" style={{ color: "#52525b" }}>Your Multi-Agent Intelligence System</p>
            </div>

            {/* ✅ FIX: suggestions call send() directly with text */}
            <div className="grid grid-cols-2 gap-2 w-full max-w-sm">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  onClick={() => send(s.text)}   /* ← FIXED */
                  disabled={loading}
                  className="flex items-center gap-2 p-3 rounded-2xl text-left text-xs disabled:opacity-40 disabled:cursor-not-allowed"
                  style={{ backgroundColor: "#1a1a1d", border: "1px solid #27272a", color: "#71717a" }}
                  onMouseEnter={e => { gsap.to(e.currentTarget, { scale: 1.03, duration: 0.12 }); e.currentTarget.style.borderColor = "#8b5cf644"; }}
                  onMouseLeave={e => { gsap.to(e.currentTarget, { scale: 1,    duration: 0.12 }); e.currentTarget.style.borderColor = "#27272a"; }}
                >
                  <span className="text-sm">{s.icon}</span>
                  <span className="leading-snug">{s.text}</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex flex-col gap-5 max-w-2xl mx-auto">
            {messages.map(msg => (
              <Bubble
                key={msg.id}
                message={msg}
                streamText={streamText}
                isStreamingThis={msg.id === streamingMsgId}
              />
            ))}
            {/* ✅ Loader: appears right after user message, before streaming starts */}
            {loading && !streamingMsgId && <TypingDots />}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-6 py-4 border-t shrink-0" style={{ borderColor: "#27272a" }}>
        <div className="max-w-2xl mx-auto">
          <div
            ref={inputWrapRef}
            className="flex items-end gap-3 rounded-2xl px-4 py-3"
            style={{ backgroundColor: "#1a1a1d", border: "1px solid #27272a" }}
          >
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={e => {
                setInput(e.target.value);
                e.target.style.height = "auto";
                e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
              }}
              onKeyDown={handleKey}
              onFocus={handleFocus}
              onBlur={handleBlur}
              disabled={loading}
              placeholder="Ask anything…"
              className="flex-1 resize-none bg-transparent outline-none text-sm leading-relaxed disabled:opacity-50"
              style={{ color: "#e4e4e7", caretColor: "#8b5cf6", maxHeight: "120px" }}
            />
            <button
              ref={sendBtnRef}
              onClick={() => send()}
              disabled={!input.trim() || loading}
              className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0 disabled:opacity-30 disabled:cursor-not-allowed"
              style={{ backgroundColor: input.trim() && !loading ? "#8b5cf6" : "#27272a" }}
              onMouseEnter={e => { if (!loading && input.trim()) gsap.to(e.currentTarget, { scale: 1.1, duration: 0.1 }); }}
              onMouseLeave={e => gsap.to(e.currentTarget, { scale: 1, duration: 0.1 })}
            >
              <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
                <path d="M12 7L2 2L5 7L2 12L12 7Z" fill="white" />
              </svg>
            </button>
          </div>
          <p className="text-center text-xs mt-2" style={{ color: "#3f3f46" }}>
            <kbd className="px-1 rounded" style={{ backgroundColor: "#1a1a1d", color: "#52525b" }}>Enter</kbd> send ·{" "}
            <kbd className="px-1 rounded" style={{ backgroundColor: "#1a1a1d", color: "#52525b" }}>Shift+Enter</kbd> newline
          </p>
        </div>
      </div>
    </main>
  );
}