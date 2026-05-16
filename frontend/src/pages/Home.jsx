// Home.jsx — wires ThinkingPipeline state into ChatWindow
import { useState, useCallback, useRef } from "react";
import Sidebar      from "../components/Sidebar";
import ChatWindow   from "../components/ChatWindow";
import AgentPanel   from "../components/AgentPanel";
import useChat      from "../hooks/useChat";
import useAgents    from "../hooks/useAgents";
import useStreamer   from "../hooks/useStreamer";
import { parseResponse }    from "../utils/parseResponse";
import { parsePlanToStates } from "../utils/parsePlan";

const STEP_DURATION_MS = 1400; // how long each thinking step stays active

export default function Home() {
  const {
    chats, activeChat, activeChatId,
    newChat, switchChat, deleteChat,
    addMessage, updateMessage,
  } = useChat();

  const { agentStates, pipelineStage, runPipeline, resetPipeline } = useAgents();
  const { text: streamText, streaming, stream, cancel }            = useStreamer();

  const [loading,         setLoading]         = useState(false);
  const [streamingMsgId,  setStreamingMsgId]  = useState(null);
  const [thinkingSteps,   setThinkingSteps]   = useState([]);
  const [thinkingIdx,     setThinkingIdx]     = useState(-1);
  const [uploadState,     setUploadState]     = useState({ status: "idle", fileName: "" });

  const stepTimersRef = useRef([]);

  // ── Clear thinking timers ────────────────────────────────────────────────
  const clearStepTimers = () => {
    stepTimersRef.current.forEach(clearTimeout);
    stepTimersRef.current = [];
  };

  // ── Animate thinking steps one by one ───────────────────────────────────
  const animateThinkingSteps = useCallback((steps) => {
    clearStepTimers();
    setThinkingSteps(steps);
    setThinkingIdx(0);

    steps.forEach((_, i) => {
      const t = setTimeout(() => {
        setThinkingIdx(i);
      }, i * STEP_DURATION_MS);
      stepTimersRef.current.push(t);
    });

    // Mark all complete slightly before streaming begins
    const tDone = setTimeout(() => {
      setThinkingIdx(steps.length); // beyond last → all "done"
    }, steps.length * STEP_DURATION_MS);
    stepTimersRef.current.push(tDone);
  }, []);

  // ── Send handler ─────────────────────────────────────────────────────────
  const handleSend = useCallback(async (query) => {
    if (!query || loading) return;

    const chatId = activeChatId;
    setLoading(true);
    cancel();
    clearStepTimers();

    // 1. User message
    addMessage(chatId, "user", query);

    // 2. Empty AI placeholder (streaming will fill it)
    const aiMsgId = addMessage(chatId, "assistant", "");
    setStreamingMsgId(null);

    // 3. Optimistic fallback thinking states while waiting for backend
    const fallbackSteps = parsePlanToStates("");
    animateThinkingSteps(fallbackSteps);

    // 4. Run agent panel animation
    runPipeline();

    try {
      const res  = await fetch("http://localhost:8000/api/v1/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();

      // ✅ CRITICAL SEPARATION: extract plan vs answer
      const { answer, plan } = parseResponse(data);

      // 5. Re-derive thinking steps from actual backend plan (replaces fallback)
      if (plan) {
        clearStepTimers();
        const planSteps = parsePlanToStates(plan);
        animateThinkingSteps(planSteps);
      }

      // 6. Small delay to let last thinking step be seen before streaming starts
      await new Promise(r => setTimeout(r, 600));

      // 7. Stream only the clean answer — plan NEVER touches message state
      setStreamingMsgId(aiMsgId);
      stream(
        answer,
        (chunk) => updateMessage(chatId, aiMsgId, chunk),
        (full) => {
          updateMessage(chatId, aiMsgId, full, { done: true });
          setStreamingMsgId(null);
          setLoading(false);
          clearStepTimers();
          setThinkingIdx(thinkingSteps.length); // mark all done
          // Fade out thinking panel after brief delay
          setTimeout(() => {
            setThinkingSteps([]);
            setThinkingIdx(-1);
          }, 1800);
        }
      );
    } catch {
      const errMsg = "Connection error — is the backend running?";
      updateMessage(chatId, aiMsgId, errMsg, { done: true });
      setStreamingMsgId(null);
      setLoading(false);
      clearStepTimers();
      setThinkingSteps([]);
      setThinkingIdx(-1);
      resetPipeline();
    }
  }, [
    loading, activeChatId, addMessage, updateMessage,
    runPipeline, resetPipeline, stream, cancel,
    animateThinkingSteps, thinkingSteps.length,
  ]);

  // ── Upload ────────────────────────────────────────────────────────────────
  const handleUpload = useCallback(async (file) => {
    setUploadState({ status: "uploading", fileName: file.name });
    try {
      const form = new FormData();
      form.append("file", file);
      await fetch("http://localhost:8000/api/v1/upload", { method: "POST", body: form });
      setUploadState({ status: "done", fileName: file.name });
      setTimeout(() => setUploadState({ status: "idle", fileName: "" }), 4000);
    } catch {
      setUploadState({ status: "idle", fileName: "" });
    }
  }, []);

  return (
    <div
      className="flex h-screen w-screen overflow-hidden"
      style={{ backgroundColor: "#0f0f11", fontFamily: "'DM Sans', sans-serif" }}
    >
      <Sidebar
        chats={chats}
        activeChatId={activeChatId}
        onNewChat={newChat}
        onSwitch={switchChat}
        onDelete={deleteChat}
        onUpload={handleUpload}
        uploadState={uploadState}
      />
      <ChatWindow
        messages={activeChat?.messages ?? []}
        loading={loading}
        thinkingSteps={thinkingSteps}
        thinkingIdx={thinkingIdx}
        streamingMsgId={streamingMsgId}
        streamText={streamText}
        onSend={handleSend}
      />
      <AgentPanel
        agentStates={agentStates}
        pipelineStage={pipelineStage}
      />
    </div>
  );
}