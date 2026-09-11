import { useState } from "react";

const PARTS = [
  { label: "Subject", example: "a snow leopard" },
  { label: "Environment", example: "on a rocky Himalayan ridge" },
  { label: "Composition", example: "low angle, wide shot" },
  { label: "Lighting", example: "golden hour backlight" },
  { label: "Style", example: "documentary photography" },
  { label: "Mood", example: "still and watchful" },
  { label: "Details", example: "drifting snow, sharp fur detail" },
];

const EXAMPLE = PARTS.map((part) => part.example).join(", ");

export function PromptGuide({ onUseExample }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-lg border border-line bg-inset">
      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-3 rounded-lg px-3.5 py-2.5 text-left transition-colors hover:bg-raised/50"
      >
        <span className="text-sm font-medium text-ink">How to write a good prompt</span>
        <span
          aria-hidden="true"
          className="text-ink-muted transition-transform duration-[200ms] ease-pc"
          style={{ transform: open ? "rotate(180deg)" : undefined }}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </span>
      </button>

      {open && (
        <div className="border-t border-line px-3.5 py-3">
          <p className="text-sm text-ink-secondary">
            Stack these seven ingredients. You do not need all of them, but the more
            you give, the closer the result lands.
          </p>
          <dl className="mt-3 grid gap-x-4 gap-y-1.5 sm:grid-cols-2">
            {PARTS.map((part) => (
              <div key={part.label} className="flex gap-2 text-sm">
                <dt className="w-24 shrink-0 font-medium text-ink">{part.label}</dt>
                <dd className="min-w-0 text-ink-muted">{part.example}</dd>
              </div>
            ))}
          </dl>
          <button
            type="button"
            onClick={() => onUseExample(EXAMPLE)}
            className="mt-3 rounded-sm text-sm font-medium text-accent hover:underline"
          >
            Use this example prompt
          </button>
        </div>
      )}
    </div>
  );
}
