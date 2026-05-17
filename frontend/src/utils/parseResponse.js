// parseResponse.js — consume the structured backend response

/**
 * Parse the structured QueryResponse from the backend.
 *
 * Contract:
 *   data.response       → rendered in chat bubble ONLY
 *   data.thinking_steps → animated in ThinkingPipeline ONLY
 *   data.tools_used     → rendered as tool badges
 *   data.plan           → NEVER rendered in UI (internal metadata)
 *
 * @param {Object|string} data — raw fetch response body
 * @returns {{ answer, thinkingSteps, toolsUsed, plan }}
 */
export function parseResponse(data) {
  if (!data || typeof data === "string") {
    return {
      answer: typeof data === "string" ? data : "No response.",
      thinkingSteps: [],
      toolsUsed: [],
      plan: "",
    };
  }

  return {
    answer:        (data.response       ?? "").trim(),
    thinkingSteps: Array.isArray(data.thinking_steps) ? data.thinking_steps : [],
    toolsUsed:     Array.isArray(data.tools_used)     ? data.tools_used     : [],
    plan:          (data.plan           ?? ""),    // metadata — DO NOT render
  };
}

// Tool badge metadata
const TOOL_META = {
  web_search:  { icon: "🌐", label: "Web Search"     },
  rag:         { icon: "📚", label: "Knowledge Base" },
  calculator:  { icon: "🧮", label: "Calculator"     },
  date:        { icon: "📅", label: "Date Tool"      },
  equation:    { icon: "∑",  label: "Equation Solver"},
};

/**
 * Convert tools_used key list into badge objects for rendering.
 * @param {string[]} toolKeys
 * @returns {Array<{key, icon, label}>}
 */
export function resolveToolBadges(toolKeys) {
  if (!Array.isArray(toolKeys)) return [];
  return toolKeys
    .map(k => ({ key: k, ...(TOOL_META[k] ?? { icon: "🔧", label: k }) }))
    .filter(Boolean);
}

/**
 * Legacy: detect tools from answer text when backend doesn't return tools_used.
 * Only used as a fallback.
 */
export function detectTools(text) {
  if (!text) return [];
  const tools = [];
  if (/title:|web search|search result|\[\d+\]/i.test(text))             tools.push("web_search");
  if (/\b\d+\s*[+\-*/]\s*\d+|calculator|equation|sympy/i.test(text))    tools.push("calculator");
  if (/knowledge base|retrieved|rag|document/i.test(text))               tools.push("rag");
  if (/today|current date|monday|tuesday|wednesday|thursday|friday/i.test(text)) tools.push("date");
  return tools.map(k => ({ key: k, ...(TOOL_META[k] ?? { icon: "🔧", label: k }) }));
}