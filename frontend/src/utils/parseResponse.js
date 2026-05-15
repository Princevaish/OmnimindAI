// parseResponse.js — extract clean answer + plan from backend response
export function parseResponse(data) {
  // data may be { response, plan } or just a string
  const raw = typeof data === "string" ? data : data?.response ?? "";
  const plan = typeof data === "string" ? "" : data?.plan ?? "";

  // Strip "Plan:\n..." prefix that some backends return inside response
  const cleaned = raw
    .replace(/^plan:\s*/i, "")
    .replace(/^#+\s*plan\s*\n+/im, "")
    .trim();

  return { answer: cleaned, plan };
}

export function detectTools(text) {
  if (!text) return [];
  const lower = text.toLowerCase();
  const tools = [];
  if (/title:|web search|search result/i.test(lower)) tools.push({ key: "web",  icon: "🌐", label: "Web Search"     });
  if (/\b\d+\s*[+\-*/]\s*\d+|calculator|equation|sympy/i.test(lower))  tools.push({ key: "math", icon: "🧮", label: "Calculator"     });
  if (/knowledge base|retrieved|rag|document/i.test(lower))              tools.push({ key: "rag",  icon: "📚", label: "Knowledge Base" });
  if (/today|current date|monday|tuesday|wednesday|thursday|friday|saturday|sunday/i.test(lower)) tools.push({ key: "date", icon: "📅", label: "Date Tool" });
  return tools;
}