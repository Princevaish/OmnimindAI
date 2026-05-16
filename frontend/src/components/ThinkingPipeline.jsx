// ThinkingPipeline.jsx — premium animated thinking state visualization
import { useRef, useEffect, useState } from "react";
import { gsap } from "gsap";

// ── Thinking dot loader ──────────────────────────────────────────────────────
function ThinkingDots() {
  return (
    <div className="flex items-center gap-1">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="block w-1 h-1 rounded-full"
          style={{
            backgroundColor: "#8b5cf6",
            animation: `tp-dot 1.4s ease-in-out ${i * 0.18}s infinite`,
          }}
        />
      ))}
    </div>
  );
}

// ── Single thinking step row ─────────────────────────────────────────────────
function ThinkingStep({ step, status, index }) {
  const ref  = useRef(null);
  const barRef = useRef(null);

  // status: "waiting" | "active" | "done"
  useEffect(() => {
    if (!ref.current) return;
    gsap.killTweensOf(ref.current);

    if (status === "active") {
      // Entrance
      gsap.fromTo(ref.current,
        { opacity: 0, x: -10 },
        { opacity: 1, x: 0, duration: 0.35, ease: "power2.out" }
      );
      // Continuous violet glow pulse
      gsap.to(ref.current, {
        boxShadow: "0 0 18px rgba(139,92,246,0.25)",
        duration: 0.9, repeat: -1, yoyo: true, ease: "sine.inOut",
      });
    } else if (status === "done") {
      gsap.killTweensOf(ref.current);
      gsap.to(ref.current, {
        boxShadow: "none",
        opacity: 0.55,
        duration: 0.4,
        ease: "power1.inOut",
      });
    } else {
      // waiting — hidden until active
      gsap.set(ref.current, { opacity: 0 });
    }
  }, [status]);

  // Progress bar fill on active
  useEffect(() => {
    if (!barRef.current) return;
    if (status === "active") {
      gsap.fromTo(barRef.current,
        { scaleX: 0 },
        { scaleX: 1, duration: 2.2, ease: "power1.inOut", transformOrigin: "left center" }
      );
    } else if (status === "done") {
      gsap.set(barRef.current, { scaleX: 1 });
    } else {
      gsap.set(barRef.current, { scaleX: 0 });
    }
  }, [status]);

  const isActive = status === "active";
  const isDone   = status === "done";

  return (
    <div
      ref={ref}
      className="relative flex items-center gap-3 px-4 py-3 rounded-2xl overflow-hidden"
      style={{
        backgroundColor: isActive ? "rgba(139,92,246,0.07)" : "transparent",
        border: `1px solid ${isActive ? "rgba(139,92,246,0.25)" : "transparent"}`,
        opacity: 0,
      }}
    >
      {/* Progress bar underline */}
      <div
        ref={barRef}
        className="absolute bottom-0 left-0 h-px w-full"
        style={{
          background: "linear-gradient(90deg, #8b5cf6, transparent)",
          transformOrigin: "left center",
          scaleX: 0,
        }}
      />

      {/* Icon */}
      <span
        className="text-base shrink-0 w-7 text-center"
        style={{ filter: isActive ? "none" : "grayscale(60%)" }}
      >
        {step.icon}
      </span>

      {/* Label */}
      <span
        className="text-sm flex-1"
        style={{
          color: isActive ? "#e4e4e7" : isDone ? "#52525b" : "#3f3f46",
          fontWeight: isActive ? 500 : 400,
        }}
      >
        {step.label}
      </span>

      {/* Right indicator */}
      <div className="shrink-0">
        {isActive && <ThinkingDots />}
        {isDone && (
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M2.5 7L5.5 10L11.5 4" stroke="#22c55e" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        )}
      </div>
    </div>
  );
}

// ── Main ThinkingPipeline ────────────────────────────────────────────────────
/**
 * Props:
 *   visible  {boolean}          — whether to show the panel at all
 *   steps    {Array}            — [{icon, label}, ...]
 *   activeIdx {number}          — which step is currently running (-1 = none)
 */
export default function ThinkingPipeline({ visible, steps, activeIdx }) {
  const panelRef   = useRef(null);
  const headerRef  = useRef(null);
  const prevVisible = useRef(false);

  // Panel entrance / exit
  useEffect(() => {
    if (!panelRef.current) return;

    if (visible && !prevVisible.current) {
      gsap.fromTo(panelRef.current,
        { opacity: 0, y: -14, scaleY: 0.94 },
        { opacity: 1, y: 0, scaleY: 1, duration: 0.38, ease: "power3.out",
          transformOrigin: "top center" }
      );
    } else if (!visible && prevVisible.current) {
      gsap.to(panelRef.current, {
        opacity: 0, y: -8, scaleY: 0.96, duration: 0.28, ease: "power2.in",
        transformOrigin: "top center",
      });
    }

    prevVisible.current = visible;
  }, [visible]);

  // Pulse the "Thinking" header text while running
  useEffect(() => {
    if (!headerRef.current) return;
    if (visible && activeIdx >= 0) {
      gsap.to(headerRef.current, {
        opacity: 0.55, duration: 0.7, repeat: -1, yoyo: true, ease: "sine.inOut",
      });
    } else {
      gsap.killTweensOf(headerRef.current);
      gsap.set(headerRef.current, { opacity: 1 });
    }
  }, [visible, activeIdx]);

  if (!visible && !prevVisible.current) return null;

  const allDone = activeIdx >= steps.length;

  return (
    <div
      ref={panelRef}
      className="mx-4 mt-4 rounded-2xl overflow-hidden shrink-0"
      style={{
        backgroundColor: "#111114",
        border: "1px solid #27272a",
        opacity: 0,
      }}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3 border-b"
        style={{ borderColor: "#1f1f23" }}
      >
        <div className="flex items-center gap-2.5">
          {/* Animated orb */}
          <div
            className="relative w-2.5 h-2.5"
            style={{ flexShrink: 0 }}
          >
            <span
              className="absolute inset-0 rounded-full"
              style={{
                backgroundColor: allDone ? "#22c55e" : "#8b5cf6",
                animation: allDone ? "none" : "tp-orb-ring 1.5s ease-out infinite",
                opacity: 0.35,
              }}
            />
            <span
              className="absolute inset-0.5 rounded-full"
              style={{ backgroundColor: allDone ? "#22c55e" : "#8b5cf6" }}
            />
          </div>

          <span
            ref={headerRef}
            className="text-xs font-semibold uppercase tracking-widest"
            style={{ color: allDone ? "#22c55e" : "#8b5cf6" }}
          >
            {allDone ? "Complete" : "Thinking"}
          </span>
        </div>

        <span className="text-xs tabular-nums" style={{ color: "#3f3f46" }}>
          {Math.min(activeIdx, steps.length)}/{steps.length}
        </span>
      </div>

      {/* Steps */}
      <div className="px-2 py-2 flex flex-col gap-0.5">
        {steps.map((step, i) => (
          <ThinkingStep
            key={step.label + i}
            step={step}
            index={i}
            status={
              i < activeIdx  ? "done"
            : i === activeIdx ? "active"
            :                  "waiting"
            }
          />
        ))}
      </div>

      {/* Keyframes injected once */}
      <style>{`
        @keyframes tp-dot {
          0%,100% { transform: translateY(0);   opacity: 0.35; }
          50%      { transform: translateY(-4px); opacity: 1;    }
        }
        @keyframes tp-orb-ring {
          0%   { transform: scale(1);   opacity: 0.35; }
          70%  { transform: scale(2.4); opacity: 0;    }
          100% { transform: scale(2.4); opacity: 0;    }
        }
      `}</style>
    </div>
  );
}