// Home.jsx — consumes structured QueryResponse; plan never reaches chat state
import { useState, useCallback, useRef } from "react";
import Sidebar    from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";
import AgentPanel from "../components/AgentPanel";
import useChat    from "../hooks/useChat";
import useAgents  from "../hooks/useAgents";
import useStreamer from "../hooks/useStreamer";
import { parseResponse } from "../utils/parseResponse";

const STEP_MS = 1300; // ms per thinking step

export default function Home() {
  const {
    chats, activeChat, activeChatId,
    newChat, switchChat, deleteChat,
    addMessage, updateMessage,
  } = useChat();

  const { agentStates, pipelineStage, runPipeline, resetPipeline } = useAgents();
  const { text: streamText, stream, cancel }                        = useStreamer();

  const [loading,        setLoading]        = useState(false);
  const [streamingMsgId, setStreamingMsgId] = useState(null);
  const [thinkingSteps,  setThinkingSteps]  = useState([]);
  const [thinkingIdx,    setThinkingIdx]    = useState(-1);
  const [uploadState,    setUploadState]    = useState({ status: "idle", fileName: "" });

  const timers = useRef([]);
  const clearTimers = () => { timers.current.forEach(clearTimeout); timers.current = []; };

  const animateSteps = useCallback((steps) => {
    clearTimers();
    setThinkingSteps(steps);
    setThinkingIdx(0);
    steps.forEach((_, i) => {
      const t = setTimeout(() => setThinkingIdx(i), i * STEP_MS);
      timers.current.push(t);
    });
    const tDone = setTimeout(() => setThinkingIdx(steps.length), steps.length * STEP_MS);
    timers.current.push(tDone);
  }, []);

  const handleSend = useCallback(async (query) => {
    if (!query || loading) return;

    const chatId = activeChatId;
    setLoading(true);
    cancel();
    clearTimers();

    // 1. Optimistic thinking states while fetch is in-flight
    animateSteps(["Analyzing query", "Routing tools", "Processing request", "Refining answer"]);

    addMessage(chatId, "user", query);
    const aiMsgId = addMessage(chatId, "assistant", "");
    setStreamingMsgId(null);
    runPipeline();

    try {
      const res  = await fetch("http://localhost:8000/api/v1/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();

      // ✅ STRUCTURED RESPONSE — plan is metadata, never touches message state
      const { answer, thinkingSteps, toolsUsed, plan } = parseResponse(data);

      // 2. Replace optimistic steps with backend-derived steps
      if (thinkingSteps.length > 0) {
        clearTimers();
        animateSteps(thinkingSteps);
      }

      // 3. Brief pause so last thinking step is visible before streaming
      await new Promise(r => setTimeout(r, 500));

      // 4. Stream ONLY the answer — plan never touches addMessage/updateMessage
      setStreamingMsgId(aiMsgId);
      stream(
        answer,
        (chunk) => updateMessage(chatId, aiMsgId, chunk),
        (full)  => {
          // Store answer + tool metadata on the message (not plan)
          updateMessage(chatId, aiMsgId, full, { done: true, toolsUsed });
          setStreamingMsgId(null);
          setLoading(false);
          clearTimers();
          setThinkingIdx(thinkingSteps.length);
          setTimeout(() => { setThinkingSteps([]); setThinkingIdx(-1); }, 2000);
        }
      );
    } catch {
      const errMsg = "Connection error — is the backend running?";
      updateMessage(chatId, aiMsgId, errMsg, { done: true });
      setStreamingMsgId(null);
      setLoading(false);
      clearTimers();
      setThinkingSteps([]);
      setThinkingIdx(-1);
      resetPipeline();
    }
  }, [loading, activeChatId, addMessage, updateMessage, runPipeline, resetPipeline,
      stream, cancel, animateSteps]);

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
        chats={chats} activeChatId={activeChatId}
        onNewChat={newChat} onSwitch={switchChat}
        onDelete={deleteChat} onUpload={handleUpload}
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
      <AgentPanel agentStates={agentStates} pipelineStage={pipelineStage} />
    </div>
  );
}