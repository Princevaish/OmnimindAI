// PipelineStrip.jsx
import { useRef, useEffect } from "react";
import { gsap } from "gsap";

const STAGES = [
  { id: "planner", label: "Planner", color: "#8b5cf6" },
  { id: "research", label: "Research", color: "#06b6d4" },
  { id: "critic", label: "Critic", color: "#f59e0b" },
];

export default function PipelineStrip({ pipelineStage, visible }) {
  const stripRef = useRef(null);

  useEffect(() => {
    if (!stripRef.current) return;
    if (visible) {
      gsap.fromTo(stripRef.current,
        { opacity: 0, y: -8, height: 0 },
        { opacity: 1, y: 0, height: "auto", duration: 0.3, ease: "power2.out" }
      );
    } else {
      gsap.to(stripRef.current, { opacity: 0, y: -4, duration: 0.25, ease: "power2.in" });
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <div
      ref={stripRef}
      className="mx-4 mt-4 rounded-2xl px-4 py-3 flex items-center gap-2"
      style={{
        backgroundColor: "#141417",
        border: "1px solid #27272a",
        opacity: 0,
      }}
    >
      <span className="text-xs mr-1" style={{ color: "#52525b" }}>Running:</span>
      {STAGES.map((stage, i) => {
        const state = (() => {
          if (pipelineStage === "done") return "done";
          const stageIdx = STAGES.findIndex(s => s.id === pipelineStage);
          const myIdx = i;
          if (myIdx < stageIdx) return "done";
          if (myIdx === stageIdx) return "active";
          return "pending";
        })();

        return (
          <div key={stage.id} className="flex items-center gap-2">
            <div className="flex items-center gap-1.5">
              <span
                className="w-2 h-2 rounded-full transition-all duration-300"
                style={{
                  backgroundColor:
                    state === "active"
                      ? stage.color
                      : state === "done"
                      ? "#22c55e"
                      : "#27272a",
                  boxShadow:
                    state === "active" ? `0 0 6px ${stage.color}` : "none",
                }}
              />
              <span
                className="text-xs font-medium transition-colors duration-300"
                style={{
                  color:
                    state === "active"
                      ? stage.color
                      : state === "done"
                      ? "#22c55e"
                      : "#3f3f46",
                }}
              >
                {stage.label}
              </span>
            </div>
            {i < STAGES.length - 1 && (
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" style={{ color: "#27272a" }}>
                <path d="M2 5H8M8 5L5 2M8 5L5 8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            )}
          </div>
        );
      })}
    </div>
  );
}