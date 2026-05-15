// useChatHistory.js
import { useState, useCallback } from "react";

const generateId = () => `chat_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;

const createChat = (title = "New Chat") => ({
  id: generateId(),
  title,
  messages: [],
  createdAt: Date.now(),
});

export default function useChatHistory() {
  const [chats, setChats] = useState(() => {
    const first = createChat("New Chat");
    return [first];
  });
  const [activeChatId, setActiveChatId] = useState(() => {
    const first = createChat("New Chat");
    return first.id;
  });

  // Derived active chat
  const activeChat = chats.find(c => c.id === activeChatId) ?? chats[0];

  const newChat = useCallback(() => {
    const chat = createChat("New Chat");
    setChats(prev => [chat, ...prev]);
    setActiveChatId(chat.id);
    return chat.id;
  }, []);

  const switchChat = useCallback((id) => {
    setActiveChatId(id);
  }, []);

  const addMessage = useCallback((chatId, message) => {
    setChats(prev =>
      prev.map(chat => {
        if (chat.id !== chatId) return chat;
        const messages = [...chat.messages, message];
        // Auto-title: use first user message (truncated)
        const title =
          chat.title === "New Chat" && message.role === "user"
            ? message.content.slice(0, 36) + (message.content.length > 36 ? "…" : "")
            : chat.title;
        return { ...chat, messages, title };
      })
    );
  }, []);

  const updateLastAssistantMessage = useCallback((chatId, content) => {
    setChats(prev =>
      prev.map(chat => {
        if (chat.id !== chatId) return chat;
        const messages = [...chat.messages];
        const lastIdx = messages.length - 1;
        if (messages[lastIdx]?.role === "assistant") {
          messages[lastIdx] = { ...messages[lastIdx], content };
        }
        return { ...chat, messages };
      })
    );
  }, []);

  const deleteChat = useCallback((id) => {
    setChats(prev => {
      const next = prev.filter(c => c.id !== id);
      if (next.length === 0) {
        const fresh = createChat("New Chat");
        setActiveChatId(fresh.id);
        return [fresh];
      }
      if (id === activeChatId) setActiveChatId(next[0].id);
      return next;
    });
  }, [activeChatId]);

  return {
    chats,
    activeChatId,
    activeChat,
    newChat,
    switchChat,
    addMessage,
    updateLastAssistantMessage,
    deleteChat,
  };
}