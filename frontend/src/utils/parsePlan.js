// parsePlan.js — convert raw backend plan text into animated UI thinking states

// Keyword → display state mapping (checked in order, first match wins)
const RULE_MAP = [
  // Intent / understanding
  { patterns: [/understand|analyz|interpret|process.*query|break.*down/i],
    icon: "🧠", label: "Understanding the query" },

  // Date / time
  { patterns: [/current.*date|today|time|calendar/i],
    icon: "📅", label: "Checking current date" },

  // Math / calculation
  { patterns: [/calculat|math|equation|sympy|arithmetic|comput|formula|algebra/i],
    icon: "🧮", label: "Running calculations" },

  // Web search
  { patterns: [/web.*search|internet|tavily|live.*data|search.*source|real.?time/i],
    icon: "🌐", label: "Searching web sources" },

  // RAG / knowledge base
  { patterns: [/retriev|vector|rag|knowledge.*base|document|chroma|embed/i],
    icon: "📚", label: "Retrieving context" },

  // Planning / reasoning
  { patterns: [/plan|step.by.step|decompos|reason|strateg/i],
    icon: "🗺️", label: "Building reasoning plan" },

  // Research / gather
  { patterns: [/gather|research|collect|information|source/i],
    icon: "🔍", label: "Researching sources" },

  // Synthesis / combining
  { patterns: [/combin|synthesiz|integrat|merging|consolidat/i],
    icon: "⚗️", label: "Synthesizing context" },

  // Evaluation / critique
  { patterns: [/evaluat|critic|review|refine|improv|verify|quality/i],
    icon: "✦", label: "Refining the answer" },

  // Formatting / writing
  { patterns: [/generat|formulat|construct|write|draft|compil/i],
    icon: "✨", label: "Composing response" },
];

const FALLBACK_STATES = [
  { icon: "🧠", label: "Understanding the query" },
  { icon: "🔍", label: "Researching sources" },
  { icon: "⚗️", label: "Synthesizing context" },
  { icon: "✨", label: "Composing response" },
];

/**
 * Convert a raw plan string from the backend into a deduplicated list of
 * UI-friendly thinking states.
 *
 * @param {string} plan - Raw plan text from backend response
 * @returns {Array<{icon: string, label: string}>}
 */
export function parsePlanToStates(plan) {
  if (!plan || typeof plan !== "string" || plan.trim().length === 0) {
    return FALLBACK_STATES;
  }

  // Split on newlines, numbered prefixes, bullet points, or "Step N" markers
  const lines = plan
    .split(/\n|(?:\d+[\.\)]\s)|(?:step\s+\d+[:\s])|(?:[-•*]\s)/gi)
    .map(l => l.trim())
    .filter(l => l.length > 8); // skip trivially short fragments

  const matched = [];
  const seenLabels = new Set();

  for (const line of lines) {
    for (const rule of RULE_MAP) {
      if (rule.patterns.some(p => p.test(line))) {
        if (!seenLabels.has(rule.label)) {
          matched.push({ icon: rule.icon, label: rule.label });
          seenLabels.add(rule.label);
        }
        break; // first rule wins per line
      }
    }
  }

  // Always end with "Composing response" if not already present
  const composing = { icon: "✨", label: "Composing response" };
  if (!seenLabels.has(composing.label)) matched.push(composing);

  return matched.length >= 2 ? matched : FALLBACK_STATES;
}