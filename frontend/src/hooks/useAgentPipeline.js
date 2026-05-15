// useAgentPipeline.js
import { useState, useCallback } from "react";

export const AGENT_IDS = ["planner", "research", "critic"];

const defaultStates = () =>
  Object.fromEntries(AGENT_IDS.map(id => [id, "idle"]));

// Status: idle | active | thinking | done
export default function useAgentPipeline() {
  const [agentStates, setAgentStates] = useState(defaultStates());
  const [pipelineStage, setPipelineStage] = useState(null); // null | 'planner' | 'research' | 'critic' | 'done'

  const setAgent = useCallback((id, status) => {
    setAgentStates(prev => ({ ...prev, [id]: status }));
  }, []);

  const runPipelineAnimation = useCallback((doneCallback) => {
    const stages = AGENT_IDS;
    setPipelineStage(stages[0]);

    // Reset all
    setAgentStates(defaultStates());

    let i = 0;
    const step = () => {
      if (i >= stages.length) {
        setPipelineStage("done");
        setAgentStates(prev => Object.fromEntries(Object.keys(prev).map(k => [k, "done"])));
        doneCallback?.();
        return;
      }
      const current = stages[i];
      // Mark previous done
      if (i > 0) setAgent(stages[i - 1], "done");
      // Thinking first, then active
      setAgent(current, "thinking");
      setPipelineStage(current);
      setTimeout(() => {
        setAgent(current, "active");
        i++;
        // Each stage: 900ms thinking + 600ms active
        setTimeout(step, 600);
      }, 900);
    };

    step();
  }, [setAgent]);

  const resetPipeline = useCallback(() => {
    setAgentStates(defaultStates());
    setPipelineStage(null);
  }, []);

  return { agentStates, pipelineStage, runPipelineAnimation, resetPipeline };
}