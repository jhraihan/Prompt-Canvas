import { useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Alert } from "../../components/ui/Alert";
import { SparkIcon } from "../../components/ui/Icons";
import { api } from "../../lib/api";
import { formatSize } from "../../lib/format";
import { ImagePreviewDialog } from "../history/ImagePreviewDialog";
import { QualityCards, SizeCards } from "./OptionCards";
import { PromptGuide } from "./PromptGuide";
import { SavedPrompts } from "./SavedPrompts";
import { ResultPanel } from "./ResultPanel";
import { useGeneration } from "./useGeneration";

const MAX_PROMPT = 1000;
const MIN_PROMPT = 3;

const FALLBACK_OPTIONS = {
  sizes: [
    { value: "1024x1024", label: "Square", aspect: "1024 / 1024" },
    { value: "1024x1536", label: "Portrait", aspect: "1024 / 1536" },
    { value: "1536x1024", label: "Landscape", aspect: "1536 / 1024" },
  ],
  qualities: [
    { value: "standard", label: "Standard" },
    { value: "hd", label: "High detail" },
  ],
  provider: null,
  model: null,
};

const SIZE_LABELS = {
  "1024x1024": "Square",
  "1024x1536": "Portrait",
  "1536x1024": "Landscape",
};

export function GeneratorPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const handoff = location.state ?? null;

  const [prompt, setPrompt] = useState(handoff?.prompt ?? "");
  const [size, setSize] = useState(handoff?.size ?? "1024x1024");
  const [quality, setQuality] = useState(handoff?.quality ?? "standard");
  const [options, setOptions] = useState(FALLBACK_OPTIONS);
  const [preview, setPreview] = useState(null);
  const [touched, setTouched] = useState(false);
  const [quota, setQuota] = useState(null);
  const [savedKey, setSavedKey] = useState(0);

  const promptRef = useRef(null);
  const { status, image, error, isGenerating, generate, dismissError } = useGeneration();

  useEffect(() => {
    if (!handoff?.prompt) return;

    navigate(location.pathname, { replace: true, state: null });
    promptRef.current?.focus();
  }, [handoff?.prompt, navigate, location.pathname]);

  useEffect(() => {
    let cancelled = false;
    api
      .quota()
      .then((result) => {
        if (!cancelled) setQuota(result.quota);
      })
      .catch(() => {

      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    api
      .options()
      .then((result) => {
        if (!cancelled) setOptions(result);
      })
      .catch(() => {

      });
    return () => {
      cancelled = true;
    };
  }, []);

  const trimmed = prompt.trim();
  const tooShort = touched && trimmed.length > 0 && trimmed.length < MIN_PROMPT;
  const empty = touched && trimmed.length === 0;
  const overLimit = prompt.length > MAX_PROMPT;

  const promptError = empty
    ? "Describe the image you want to generate."
    : tooShort
      ? `Add a little more detail (at least ${MIN_PROMPT} characters).`
      : overLimit
        ? `Prompts are limited to ${MAX_PROMPT} characters.`
        : (error?.fieldError("prompt") ?? null);

  const canSubmit = trimmed.length >= MIN_PROMPT && !overLimit && !isGenerating;

  const submit = useCallback(async () => {
    if (!canSubmit) return;
    const result = await generate({ prompt: trimmed, size, quality });

    if (result?.quota) setQuota(result.quota);
  }, [canSubmit, generate, trimmed, size, quality]);

  function onSubmit(event) {
    event.preventDefault();
    setTouched(true);
    if (!canSubmit) {
      promptRef.current?.focus();
      return;
    }
    void submit();
  }

  function onPromptKeyDown(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
      event.preventDefault();
      setTouched(true);
      void submit();
    }
  }

  const counterTone =
    prompt.length > MAX_PROMPT
      ? "text-danger"
      : prompt.length > MAX_PROMPT * 0.9
        ? "text-warning"
        : "text-ink-muted";

  return (
    <>
            <div className="pc-reveal pc-reveal-1 mb-7">
        <h1 className="text-3xl font-bold leading-[1.05] tracking-[-0.03em] text-ink">
          Imagine it.{" "}
          <span className="pc-gradient-text">Generate it.</span>
        </h1>
        <p className="mt-2.5 max-w-xl text-base text-ink-secondary">
          Describe what you want to see. Prompt Canvas turns the description
          into an image in seconds.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,27rem)_minmax(0,1fr)] xl:gap-8">
        <form
          onSubmit={onSubmit}
          noValidate
          className="pc-reveal pc-reveal-2 flex h-fit flex-col gap-4"
        >
                    <div className="pc-composer pc-glow-panel overflow-hidden rounded-2xl shadow-md">
            <div className="flex items-center justify-between gap-3 px-4 pt-3.5">
              <label
                htmlFor="prompt-input"
                className="flex items-center gap-2 text-sm font-semibold text-ink"
              >
                <SparkIcon size={15} className="text-accent" />
                Describe your image
              </label>
              <span className={`text-xs tabular-nums ${counterTone}`}>
                {prompt.length} / {MAX_PROMPT}
              </span>
            </div>

            <textarea
              id="prompt-input"
              ref={promptRef}
              name="prompt"
              value={prompt}
              maxLength={MAX_PROMPT + 100}
              aria-describedby={promptError ? "prompt-error" : "prompt-hint"}
              aria-invalid={promptError ? true : undefined}
              placeholder="A futuristic city at sunset, seen from a rooftop, warm haze, cinematic wide shot"
              onChange={(event) => setPrompt(event.target.value)}
              onBlur={() => setTouched(true)}
              onKeyDown={onPromptKeyDown}
              className="min-h-36 w-full resize-y border-0 bg-transparent px-4 py-3 text-base leading-relaxed text-ink outline-none placeholder:text-ink-muted"
            />

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-line px-4 py-2.5">
              {promptError ? (
                <p id="prompt-error" role="alert" className="text-sm text-danger">
                  {promptError}
                </p>
              ) : (
                <p id="prompt-hint" className="text-xs text-ink-muted">
                  Subject, setting, lighting, style
                </p>
              )}
              <span className="text-xs text-ink-muted">
                <kbd className="font-mono">Ctrl</kbd> +{" "}
                <kbd className="font-mono">Enter</kbd>
              </span>
            </div>
          </div>

          <PromptGuide
            onUseExample={(example) => {
              setPrompt(example);
              promptRef.current?.focus();
            }}
          />

          <SavedPrompts
            currentPrompt={prompt}
            size={size}
            quality={quality}
            refreshKey={savedKey}
            onUse={(entry) => {
              setPrompt(entry.prompt);
              if (entry.size) setSize(entry.size);
              if (entry.quality) setQuality(entry.quality);
              setSavedKey((current) => current + 1);
              promptRef.current?.focus();
            }}
          />

                    <div className="rounded-2xl border border-line bg-surface p-4 shadow-sm">
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-2">
                <span className="text-sm font-semibold text-ink">Image size</span>
                <SizeCards
                  value={size}
                  onChange={setSize}
                  disabled={isGenerating}
                  options={options.sizes.map((option) => ({
                    value: option.value,
                    label: SIZE_LABELS[option.value] ?? option.label,
                    detail: formatSize(option.value),
                  }))}
                />
              </div>

              <div className="flex flex-col gap-2">
                <span className="text-sm font-semibold text-ink">Quality</span>
                <QualityCards
                  value={quality}
                  onChange={setQuality}
                  disabled={isGenerating}
                  options={options.qualities.map((option) => ({
                    value: option.value,
                    label: option.label,
                    detail: option.value === "hd" ? "More steps" : "Faster",
                  }))}
                />
              </div>
            </div>
          </div>

          {error && error.status === 429 && (
            <Alert tone="warning" title="Slow down a moment">
              {error.message}
            </Alert>
          )}

          <Button
            type="submit"
            variant="primary"
            size="lg"
            fullWidth
            className="shadow-glow"
            loading={isGenerating}
            loadingLabel="Generating..."
            disabled={!canSubmit}
            icon={<SparkIcon size={17} />}
          >
            Generate image
          </Button>

          {quota && (
            <div className="flex items-center gap-2.5 px-1">
              <span
                aria-hidden="true"
                className="h-1.5 flex-1 overflow-hidden rounded-full bg-inset"
              >
                <span
                  className="block h-full rounded-full bg-accent transition-[width] duration-[360ms] ease-pc"
                  style={{
                    width: `${Math.round((quota.remaining / quota.limit) * 100)}%`,
                  }}
                />
              </span>
              <span className="shrink-0 text-xs tabular-nums text-ink-muted">
                {quota.remaining} of {quota.limit} left
              </span>
            </div>
          )}
        </form>

        <ResultPanel
          status={status}
          image={image}
          error={error && error.status !== 429 ? error : null}
          pendingSize={size}
          onRetry={() => void submit()}
          onDismissError={dismissError}
          onPreview={setPreview}
        />
      </div>

      <ImagePreviewDialog image={preview} onClose={() => setPreview(null)} />
    </>
  );
}
