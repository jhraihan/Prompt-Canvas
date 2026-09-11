import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, api } from "../../lib/api";

export function useGeneration() {
  const [status, setStatus] = useState("idle");
  const [image, setImage] = useState(null);
  const [error, setError] = useState(null);
  const inFlight = useRef(null);
  const mounted = useRef(true);

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      inFlight.current?.abort();
    };
  }, []);

  const generate = useCallback(async (input) => {
    if (inFlight.current) return null;

    const controller = new AbortController();
    inFlight.current = controller;
    setStatus("generating");
    setError(null);

    try {
      const result = await api.generate(input, controller.signal);
      if (!mounted.current) return null;
      setImage(result);
      setStatus("success");
      return result;
    } catch (caught) {
      if (!mounted.current || controller.signal.aborted) return null;
      setError(
        caught instanceof ApiError
          ? caught
          : new ApiError(0, "error", "Could not generate the image. Please try again."),
      );
      setStatus("error");
      return null;
    } finally {
      if (inFlight.current === controller) inFlight.current = null;
    }
  }, []);

  const dismissError = useCallback(() => {
    setError(null);
    setStatus((current) => (current === "error" ? (image ? "success" : "idle") : current));
  }, [image]);

  const clear = useCallback(() => {
    setImage(null);
    setError(null);
    setStatus("idle");
  }, []);

  return {
    status,
    image,
    error,
    isGenerating: status === "generating",
    generate,
    dismissError,
    clear,
  };
}
