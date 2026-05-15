// useAgents.js — agent state machine + optional WebSocket integration
import { useState, useCallback, useRef, useEffect } from "react";

export const AGENTS = [
  { id: "planner",  label: "Planner",  accent: "#8b5cf6", glow: "rgba(139,92,246,0.25)" },
  { id: "research", label: "Research", accent: "#06b6d4", glow: "rgba(6,182,212,0.25)"   },
  { id: "critic",   label: "Critic",   accent: "#f59e0b", glow: "rgba(245,158,11,0.25)"  },
];

const DEFAULT_STATES = () =>
  Object.fromEntries(AGENTS.map(a => [a.id, "idle"]));

// Durations for each agent stage (ms): thinking → active → done
const STAGE_TIMING = { thinking: 800, active: 700 };

export default function useAgents() {
  const [agentStates, setAgentStates] = useState(DEFAULT_STATES);
  const [pipelineStage, setPipelineStage] = useState(null);
  const wsRef = useRef(null);
  const timerRefs = useRef([]);

  // ── WebSocket ─────────────────────────────────────────────────────────────
  useEffect(() => {
    let ws;
    try {
      ws = new WebSocket("ws://localhost:8000/ws/agents");
      wsRef.current = ws;
      ws.onmessage = (e) => {
        try {
          const { agent, status } = JSON.parse(e.data);
          if (agent && status) {
            setAgentStates(prev => ({ ...prev, [agent]: status }));
            setPipelineStage(agent);
          }
        } catch { /* malformed */ }
      };
      ws.onerror = () => { /* silent — fallback to local animation */ };
    } catch { /* WebSocket not available in some envs */ }
    return () => { try { ws?.close(); } catch { /* ignore */ } };
  }, []);

  // ── Local animation (runs even without WS) ────────────────────────────────
  const clearTimers = () => {
    timerRefs.current.forEach(clearTimeout);
    timerRefs.current = [];
  };

  const set = useCallback((id, status) => {
    setAgentStates(prev => ({ ...prev, [id]: status }));
  }, []);

  const runPipeline = useCallback((onDone) => {
    clearTimers();
    setAgentStates(DEFAULT_STATES());
    setPipelineStage("planner");

    let offset = 0;
    AGENTS.forEach((agent, idx) => {
      const t1 = setTimeout(() => {
        if (idx > 0) set(AGENTS[idx - 1].id, "done");
        set(agent.id, "thinking");
        setPipelineStage(agent.id);
      }, offset);
      offset += STAGE_TIMING.thinking;

      const t2 = setTimeout(() => {
        set(agent.id, "active");
      }, offset);
      offset += STAGE_TIMING.active;

      timerRefs.current.push(t1, t2);
    });

    const tFinal = setTimeout(() => {
      set(AGENTS[AGENTS.length - 1].id, "done");
      setPipelineStage("done");
      onDone?.();
    }, offset);
    timerRefs.current.push(tFinal);
  }, [set]);

  const resetPipeline = useCallback(() => {
    clearTimers();
    setAgentStates(DEFAULT_STATES());
    setPipelineStage(null);
  }, []);

  return { agentStates, pipelineStage, runPipeline, resetPipeline };
}