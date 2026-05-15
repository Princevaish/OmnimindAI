// Home.jsx — wires all hooks + components, handles upload
import { useState, useCallback } from "react";
import Sidebar    from "../components/Sidebar";
import ChatWindow from "../components/ChatWindow";
import AgentPanel from "../components/AgentPanel";
import useChat    from "../hooks/useChat";
import useAgents  from "../hooks/useAgents";
import useStreamer from "../hooks/useStreamer";
import { parseResponse } from "../utils/parseResponse";

export default function Home() {
  const {
    chats, activeChat, activeChatId,
    newChat, switchChat, deleteChat,
    addMessage, updateMessage,
  } = useChat();

  const { agentStates, pipelineStage, runPipeline, resetPipeline } = useAgents();
  const { text: streamText, streaming, stream, cancel } = useStreamer();

  const [loading, setLoading]               = useState(false);
  const [streamingMsgId, setStreamingMsgId] = useState(null);
  const [uploadState, setUploadState]       = useState({ status: "idle", fileName: "" });

  // ── Send message ──────────────────────────────────────────────────────────
  const handleSend = useCallback(async (query) => {
    if (!query || loading) return;

    const chatId = activeChatId;
    setLoading(true);
    cancel();

    // 1. Add user message
    addMessage(chatId, "user", query);

    // 2. Add empty AI placeholder
    const aiMsgId = addMessage(chatId, "assistant", "");
    setStreamingMsgId(null); // loader shows until streaming begins

    // 3. Run visual pipeline
    runPipeline();

    try {
      const res  = await fetch("http://localhost:8000/api/v1/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();

      // ✅ FIX: extract clean answer, discard plan from bubble
      const { answer } = parseResponse(data);

      // 4. Stream the answer word-by-word
      setStreamingMsgId(aiMsgId);
      stream(
        answer,
        (chunk) => updateMessage(chatId, aiMsgId, chunk),          // live update
        (full)  => {
          updateMessage(chatId, aiMsgId, full, { done: true });     // final write
          setStreamingMsgId(null);
          setLoading(false);
        }
      );
    } catch (err) {
      const errMsg = "Connection error. Is the backend running?";
      updateMessage(chatId, aiMsgId, errMsg, { done: true });
      setStreamingMsgId(null);
      setLoading(false);
      resetPipeline();
    }
  }, [loading, activeChatId, addMessage, updateMessage, runPipeline, resetPipeline, stream, cancel]);

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
        pipelineStage={pipelineStage}
        loading={loading}
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