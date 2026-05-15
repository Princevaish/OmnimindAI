// AgentPanel.jsx
import { useRef, useEffect } from "react";
import { gsap } from "gsap";
import { AGENTS } from "../hooks/useAgents";

const STATUS_LABEL = { idle: "Idle", thinking: "Thinking…", active: "Active", done: "Done" };

function AgentCard({ agent, status }) {
  const cardRef = useRef(null);
  const glowRef = useRef(null);
  const dotRef  = useRef(null);

  useEffect(() => {
    const card = cardRef.current;
    const glow = glowRef.current;
    const dot  = dotRef.current;
    if (!card || !glow || !dot) return;

    gsap.killTweensOf([card, glow, dot]);

    if (status === "thinking") {
      gsap.to(card, { y: -3, duration: 1, repeat: -1, yoyo: true, ease: "sine.inOut" });
      gsap.to(card, { boxShadow: `0 0 22px ${agent.glow}`, borderColor: agent.accent + "55", duration: 0.3 });
      gsap.to(glow, { opacity: 1, duration: 0.4 });
      gsap.to(dot,  { scale: 1.6, opacity: 0.5, duration: 0.5, repeat: -1, yoyo: true, ease: "sine.inOut" });
    } else if (status === "active") {
      gsap.to(card, { y: 0, duration: 0.2 });
      gsap.to(card, { boxShadow: `0 0 32px ${agent.glow}`, borderColor: agent.accent + "88", duration: 0.3 });
      gsap.to(card, { boxShadow: `0 0 44px ${agent.glow}`, duration: 0.8, repeat: -1, yoyo: true, ease: "sine.inOut" });
      gsap.to(glow, { opacity: 0.8, duration: 0.3 });
      gsap.to(dot,  { scale: 1, opacity: 1, duration: 0.2 });
    } else if (status === "done") {
      gsap.to(card, { y: 0, boxShadow: "0 0 8px rgba(34,197,94,0.1)", borderColor: "#22c55e33", duration: 0.5 });
      gsap.to(glow, { opacity: 0, duration: 0.5 });
      gsap.to(dot,  { scale: 1, opacity: 1, duration: 0.2 });
    } else {
      gsap.to(card, { y: 0, boxShadow: "none", borderColor: "#27272a", duration: 0.4 });
      gsap.to(glow, { opacity: 0, duration: 0.3 });
      gsap.to(dot,  { scale: 1, opacity: 1, duration: 0.2 });
    }
  }, [status, agent]);

  const dotColor = status === "idle" ? "#3f3f46" : status === "done" ? "#22c55e" :
                   status === "thinking" ? "#f59e0b" : agent.accent;

  return (
    <div
      ref={cardRef}
      className="relative rounded-2xl p-4 overflow-hidden"
      style={{ backgroundColor: "#1a1a1d", border: "1px solid #27272a", willChange: "transform, box-shadow" }}
    >
      <div
        ref={glowRef}
        className="absolute inset-0 pointer-events-none rounded-2xl"
        style={{ opacity: 0, background: `radial-gradient(ellipse at 50% 0%, ${agent.glow} 0%, transparent 70%)` }}
      />
      <div className="relative z-10">
        <div className="flex items-center gap-2.5 mb-2">
          <div className="w-8 h-8 rounded-xl flex items-center justify-center" style={{ backgroundColor: agent.accent + "18" }}>
            <AgentIcon id={agent.id} color={agent.accent} />
          </div>
          <div>
            <p className="text-sm font-semibold" style={{ color: "#e4e4e7" }}>{agent.label}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span ref={dotRef} className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: dotColor, display: "inline-block" }} />
              <span className="text-xs" style={{ color: dotColor === "#3f3f46" ? "#52525b" : dotColor }}>
                {STATUS_LABEL[status] ?? "Idle"}
              </span>
            </div>
          </div>
        </div>
        <p className="text-xs leading-relaxed" style={{ color: "#3f3f46" }}>
          {agent.id === "planner"  && "Decomposes query into a reasoning plan"}
          {agent.id === "research" && "Retrieves real-time web & RAG context"}
          {agent.id === "critic"   && "Evaluates and refines the final answer"}
        </p>
      </div>
    </div>
  );
}

function AgentIcon({ id, color }) {
  if (id === "planner") return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <rect x="2" y="2" width="5" height="5" rx="1" stroke={color} strokeWidth="1.5" />
      <rect x="9" y="2" width="5" height="5" rx="1" stroke={color} strokeWidth="1.5" />
      <rect x="2" y="9" width="5" height="5" rx="1" stroke={color} strokeWidth="1.5" />
      <path d="M9 11.5H14M11.5 9V14" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
  if (id === "research") return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <circle cx="7" cy="7" r="4.5" stroke={color} strokeWidth="1.5" />
      <path d="M10.5 10.5L14 14" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
  return (
    <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
      <path d="M8 2L9.5 6.5H14L10.5 9L12 13.5L8 11L4 13.5L5.5 9L2 6.5H6.5L8 2Z" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

export default function AgentPanel({ agentStates, pipelineStage }) {
  return (
    <aside
      className="flex flex-col w-64 h-full shrink-0 border-l"
      style={{ backgroundColor: "#141417", borderColor: "#27272a" }}
    >
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center justify-between mb-1">
          <h2 className="text-sm font-semibold" style={{ color: "#f4f4f5" }}>Agents</h2>
          <span className="text-xs px-2 py-0.5 rounded-full" style={{ backgroundColor: "#1a1a1d", color: "#52525b" }}>
            {pipelineStage === "done" ? "Done" : pipelineStage ? "Running" : "Standby"}
          </span>
        </div>
        <p className="text-xs" style={{ color: "#52525b" }}>Live pipeline status</p>
      </div>

      <div className="mx-5 mb-4" style={{ height: "1px", backgroundColor: "#27272a" }} />

      <div className="flex-1 overflow-y-auto px-3 pb-4 flex flex-col gap-2.5">
        {AGENTS.map(agent => (
          <AgentCard key={agent.id} agent={agent} status={agentStates[agent.id] ?? "idle"} />
        ))}
      </div>

      {/* Flow bar */}
      <div className="mx-3 mb-4 p-3 rounded-2xl" style={{ backgroundColor: "#1a1a1d", border: "1px solid #27272a" }}>
        <p className="text-xs mb-2" style={{ color: "#52525b" }}>Pipeline flow</p>
        <div className="flex items-center gap-1">
          {AGENTS.map((agent, i) => {
            const s = agentStates[agent.id] ?? "idle";
            const lit = s === "active" || s === "thinking";
            const done = s === "done";
            return (
              <div key={agent.id} className="flex items-center gap-1 flex-1">
                <div
                  className="h-1.5 flex-1 rounded-full"
                  style={{
                    backgroundColor: done ? "#22c55e" : lit ? agent.accent : "#27272a",
                    boxShadow: lit ? `0 0 6px ${agent.glow}` : "none",
                    transition: "background-color 0.4s, box-shadow 0.4s",
                  }}
                />
                {i < AGENTS.length - 1 && (
                  <svg width="8" height="8" viewBox="0 0 8 8" fill="none" style={{ color: "#3f3f46", flexShrink: 0 }}>
                    <path d="M1 4H7M7 4L4.5 1.5M7 4L4.5 6.5" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </div>
            );
          })}
        </div>
        <div className="flex justify-between mt-1.5">
          {AGENTS.map(a => <span key={a.id} className="text-xs" style={{ color: "#3f3f46" }}>{a.label}</span>)}
        </div>
      </div>
    </aside>
  );
}