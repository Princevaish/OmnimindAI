// useStreamingText.js
import { useState, useRef, useCallback } from "react";

export default function useStreamingText() {
  const [streamingText, setStreamingText] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const intervalRef = useRef(null);

  const streamText = useCallback((fullText, onWord, onComplete) => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    const words = fullText.split(" ");
    let idx = 0;
    setStreamingText("");
    setIsStreaming(true);

    // Variable speed: faster for short words, slower at start
    intervalRef.current = setInterval(() => {
      if (idx >= words.length) {
        clearInterval(intervalRef.current);
        setIsStreaming(false);
        onComplete?.(fullText);
        return;
      }
      const chunk = words.slice(0, idx + 1).join(" ");
      setStreamingText(chunk);
      onWord?.(chunk);
      idx++;
    }, 28); // ~35 words/sec
  }, []);

  const cancelStream = useCallback(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setIsStreaming(false);
  }, []);

  return { streamingText, isStreaming, streamText, cancelStream };
}