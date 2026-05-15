// Sidebar.jsx
import { useRef, useCallback } from "react";
import { gsap } from "gsap";

function ChatItem({ chat, isActive, onSelect, onDelete }) {
  const elRef = useRef(null);

  const onEnter = () => {
    if (!isActive) gsap.to(elRef.current, { backgroundColor: "#1e1e22", duration: 0.15 });
  };
  const onLeave = () => {
    if (!isActive) gsap.to(elRef.current, { backgroundColor: "transparent", duration: 0.15 });
  };

  return (
    <li
      ref={elRef}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
      onClick={() => onSelect(chat.id)}
      className="group relative flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer"
      style={{
        backgroundColor: isActive ? "#1e1e22" : "transparent",
        boxShadow: isActive ? "inset 0 0 0 1px rgba(139,92,246,0.2)" : "none",
      }}
    >
      <div
        className="w-1 h-4 rounded-full shrink-0"
        style={{ backgroundColor: "#8b5cf6", opacity: isActive ? 1 : 0, transition: "opacity 0.2s" }}
      />
      <p className="flex-1 text-xs truncate" style={{ color: isActive ? "#e4e4e7" : "#71717a" }}>
        {chat.title}
      </p>
      <button
        onClick={e => { e.stopPropagation(); onDelete(chat.id); }}
        className="opacity-0 group-hover:opacity-100 p-1 rounded-lg transition-opacity duration-150"
        style={{ color: "#52525b" }}
      >
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
          <path d="M1.5 1.5L8.5 8.5M8.5 1.5L1.5 8.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>
    </li>
  );
}

function UploadZone({ onUpload, uploadState }) {
  const inputRef = useRef(null);

  const handleChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    onUpload(file);
    e.target.value = "";
  };

  return (
    <div className="px-3 pb-3">
      <div
        onClick={() => inputRef.current?.click()}
        className="flex items-center gap-2.5 px-3 py-2.5 rounded-xl cursor-pointer transition-colors duration-150"
        style={{
          backgroundColor: "#1a1a1d",
          border: "1px dashed #27272a",
          color: "#52525b",
        }}
        onMouseEnter={e => { e.currentTarget.style.borderColor = "#8b5cf644"; e.currentTarget.style.color = "#a1a1aa"; }}
        onMouseLeave={e => { e.currentTarget.style.borderColor = "#27272a"; e.currentTarget.style.color = "#52525b"; }}
      >
        {uploadState.status === "uploading" ? (
          <svg className="animate-spin" width="13" height="13" viewBox="0 0 13 13" fill="none">
            <circle cx="6.5" cy="6.5" r="5" stroke="#8b5cf6" strokeWidth="1.5" strokeDasharray="8 20" />
          </svg>
        ) : (
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path d="M7 1V10M3 5L7 1L11 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M1 11V13H13V11" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        )}
        <span className="text-xs truncate">
          {uploadState.status === "done"
            ? `✓ ${uploadState.fileName}`
            : uploadState.status === "uploading"
            ? "Uploading…"
            : "Upload PDF / TXT"}
        </span>
      </div>
      <input ref={inputRef} type="file" accept=".pdf,.txt" className="hidden" onChange={handleChange} />
    </div>
  );
}

export default function Sidebar({ chats, activeChatId, onNewChat, onSwitch, onDelete, onUpload, uploadState }) {
  const btnRef = useRef(null);

  const handleNew = () => {
    gsap.to(btnRef.current, {
      scale: 0.94, duration: 0.07,
      onComplete: () => gsap.to(btnRef.current, { scale: 1, duration: 0.18, ease: "back.out(2)" }),
    });
    onNewChat();
  };

  return (
    <aside
      className="flex flex-col w-64 h-full shrink-0 border-r"
      style={{ backgroundColor: "#141417", borderColor: "#27272a" }}
    >
      {/* Logo */}
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center gap-2.5 mb-5">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
            style={{ background: "linear-gradient(135deg,#8b5cf6,#6d28d9)", boxShadow: "0 0 20px rgba(139,92,246,0.4)" }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2L13 5V11L8 14L3 11V5L8 2Z" stroke="white" strokeWidth="1.5" strokeLinejoin="round" />
              <circle cx="8" cy="8" r="2" fill="white" />
            </svg>
          </div>
          <span className="text-sm font-semibold" style={{ color: "#f4f4f5" }}>OmniMind AI</span>
        </div>

        <button
          ref={btnRef}
          onClick={handleNew}
          className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl text-xs font-medium"
          style={{ backgroundColor: "#8b5cf6", color: "#fff", boxShadow: "0 0 16px rgba(139,92,246,0.3)" }}
          onMouseEnter={e => { gsap.to(e.currentTarget, { scale: 1.02, duration: 0.1 }); e.currentTarget.style.backgroundColor = "#7c3aed"; }}
          onMouseLeave={e => { gsap.to(e.currentTarget, { scale: 1, duration: 0.1 }); e.currentTarget.style.backgroundColor = "#8b5cf6"; }}
        >
          <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
            <path d="M5.5 1V10M1 5.5H10" stroke="white" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
          New Chat
        </button>
      </div>

      <div className="mx-5 mb-3" style={{ height: "1px", backgroundColor: "#27272a" }} />

      {/* History */}
      <div className="flex-1 overflow-y-auto px-3 pb-3">
        {chats.length > 0 && (
          <p className="px-3 mb-2 text-xs uppercase tracking-widest" style={{ color: "#3f3f46" }}>History</p>
        )}
        <ul className="flex flex-col gap-0.5">
          {chats.map(chat => (
            <ChatItem
              key={chat.id}
              chat={chat}
              isActive={chat.id === activeChatId}
              onSelect={onSwitch}
              onDelete={onDelete}
            />
          ))}
        </ul>
      </div>

      <div className="mx-5 mb-3" style={{ height: "1px", backgroundColor: "#27272a" }} />

      {/* Upload */}
      <UploadZone onUpload={onUpload} uploadState={uploadState} />

      {/* Footer */}
      <div
        className="px-4 py-4 border-t flex items-center gap-2.5"
        style={{ borderColor: "#27272a" }}
      >
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold"
          style={{ backgroundColor: "#27272a", color: "#8b5cf6" }}
        >U</div>
        <div>
          <p className="text-xs font-medium" style={{ color: "#e4e4e7" }}>User</p>
          <p className="text-xs" style={{ color: "#52525b" }}>Free Plan</p>
        </div>
      </div>
    </aside>
  );
}