// useChat.js — persistent chat history with localStorage
import { useState, useCallback, useEffect } from "react";

const LS_KEY = "omnimind_chats";
const LS_ACTIVE = "omnimind_active_chat";

const genId = () => `c_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
const genMsgId = () => `m_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

function makeChat(title = "New Chat") {
  return { id: genId(), title, messages: [], createdAt: Date.now() };
}

function autoTitle(text) {
  const words = text.trim().split(/\s+/);
  const sliced = words.slice(0, 7).join(" ");
  return sliced.length < text.trim().length ? sliced + "…" : sliced;
}

function loadFromStorage() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    const chats = raw ? JSON.parse(raw) : null;
    const activeId = localStorage.getItem(LS_ACTIVE);
    if (chats && chats.length > 0) return { chats, activeId: activeId ?? chats[0].id };
  } catch { /* ignore */ }
  const initial = makeChat("New Chat");
  return { chats: [initial], activeId: initial.id };
}

export default function useChat() {
  const [state, setState] = useState(() => loadFromStorage());

  // Persist every change
  useEffect(() => {
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(state.chats));
      localStorage.setItem(LS_ACTIVE, state.activeId);
    } catch { /* quota exceeded or private mode */ }
  }, [state]);

  const activeChat = state.chats.find(c => c.id === state.activeId) ?? state.chats[0];

  // ── Public API ───────────────────────────────────────────────────────────

  const newChat = useCallback(() => {
    const chat = makeChat("New Chat");
    setState(prev => ({ chats: [chat, ...prev.chats], activeId: chat.id }));
    return chat.id;
  }, []);

  const switchChat = useCallback((id) => {
    setState(prev => ({ ...prev, activeId: id }));
  }, []);

  const deleteChat = useCallback((id) => {
    setState(prev => {
      const chats = prev.chats.filter(c => c.id !== id);
      if (chats.length === 0) {
        const fresh = makeChat("New Chat");
        return { chats: [fresh], activeId: fresh.id };
      }
      const activeId = prev.activeId === id ? chats[0].id : prev.activeId;
      return { chats, activeId };
    });
  }, []);

  /** Add a message to a specific chat. Returns the generated message id. */
  const addMessage = useCallback((chatId, role, content, extra = {}) => {
    const id = genMsgId();
    setState(prev => ({
      ...prev,
      chats: prev.chats.map(chat => {
        if (chat.id !== chatId) return chat;
        const isFirstUser = role === "user" && chat.messages.filter(m => m.role === "user").length === 0;
        return {
          ...chat,
          title: isFirstUser ? autoTitle(content) : chat.title,
          messages: [...chat.messages, { id, role, content, ...extra }],
        };
      }),
    }));
    return id;
  }, []);

  /** Overwrite the content of a specific message (for streaming updates). */
  const updateMessage = useCallback((chatId, msgId, content, extra = {}) => {
    setState(prev => ({
      ...prev,
      chats: prev.chats.map(chat => {
        if (chat.id !== chatId) return chat;
        return {
          ...chat,
          messages: chat.messages.map(m =>
            m.id === msgId ? { ...m, content, ...extra } : m
          ),
        };
      }),
    }));
  }, []);

  return {
    chats: state.chats,
    activeChat,
    activeChatId: state.activeId,
    newChat,
    switchChat,
    deleteChat,
    addMessage,
    updateMessage,
  };
}