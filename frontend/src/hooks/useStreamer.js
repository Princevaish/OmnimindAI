// useStreamer.js — word-by-word streaming with cursor
import { useState, useRef, useCallback } from "react";

const WORDS_PER_SECOND = 40;
const INTERVAL_MS = Math.round(1000 / WORDS_PER_SECOND);

export default function useStreamer() {
  const [text, setText] = useState("");
  const [streaming, setStreaming] = useState(false);
  const ref = useRef(null);

  const stream = useCallback((fullText, onUpdate, onDone) => {
    if (ref.current) clearInterval(ref.current);
    const words = fullText.split(" ");
    let idx = 0;
    setText("");
    setStreaming(true);

    ref.current = setInterval(() => {
      idx++;
      const chunk = words.slice(0, idx).join(" ");
      setText(chunk);
      onUpdate?.(chunk);
      if (idx >= words.length) {
        clearInterval(ref.current);
        setStreaming(false);
        onDone?.(fullText);
      }
    }, INTERVAL_MS);
  }, []);

  const cancel = useCallback(() => {
    if (ref.current) clearInterval(ref.current);
    setStreaming(false);
  }, []);

  return { text, streaming, stream, cancel };
}