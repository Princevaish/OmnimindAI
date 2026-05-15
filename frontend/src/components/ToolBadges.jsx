// ToolBadges.jsx
const TOOL_META = {
  web_search:  { icon: "🌐", label: "Web Search" },
  calculator:  { icon: "🧮", label: "Calculator" },
  rag:         { icon: "📚", label: "Knowledge Base" },
  date:        { icon: "📅", label: "Date Tool" },
  equation:    { icon: "∑", label: "Equation Solver" },
};

function detectTools(content) {
  if (!content) return [];
  const tools = new Set();
  const lower = content.toLowerCase();
  if (lower.includes("web") || lower.includes("search") || lower.includes("title:")) tools.add("web_search");
  if (lower.match(/\b\d+\s*[+\-*/]\s*\d+/)) tools.add("calculator");
  if (lower.includes("knowledge base") || lower.includes("document")) tools.add("rag");
  if (lower.includes("today") || lower.match(/\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b/)) tools.add("date");
  if (lower.match(/[a-z]\s*=\s*\d/)) tools.add("equation");
  return [...tools];
}

export default function ToolBadges({ content, tools: explicitTools }) {
  const tools = explicitTools ?? detectTools(content);
  if (!tools.length) return null;

  return (
    <div className="flex flex-wrap gap-1.5 mb-1.5">
      {tools.map(tool => {
        const meta = TOOL_META[tool] ?? { icon: "🔧", label: tool };
        return (
          <span
            key={tool}
            className="flex items-center gap-1 px-2 py-0.5 rounded-lg text-xs"
            style={{
              backgroundColor: "#1a1a1d",
              border: "1px solid #27272a",
              color: "#71717a",
            }}
          >
            <span>{meta.icon}</span>
            <span>{meta.label}</span>
          </span>
        );
      })}
    </div>
  );
}