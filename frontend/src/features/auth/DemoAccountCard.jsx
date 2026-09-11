import { useState } from "react";

import { Button } from "../../components/ui/Button";
import { InfoIcon } from "../../components/ui/Icons";

export function DemoAccountCard({ account, onUse, disabled }) {
  const [copied, setCopied] = useState(null);

  async function copy(value, field) {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(field);
      setTimeout(() => setCopied(null), 1600);
    } catch {

    }
  }

  return (
    <div className="rounded-lg border border-line bg-inset p-3.5">
      <div className="flex items-start gap-2.5">
        <InfoIcon size={16} className="mt-0.5 shrink-0 text-ink-muted" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-ink">Try it without signing up</p>
          <p className="mt-0.5 text-xs text-ink-muted">
            A shared demo account. Anyone can use it, so its history is visible to
            every visitor.
          </p>

          <dl className="mt-2.5 flex flex-col gap-1">
            <Row
              term="Email"
              value={account.email}
              copied={copied === "email"}
              onCopy={() => void copy(account.email, "email")}
            />
            <Row
              term="Password"
              value={account.password}
              copied={copied === "password"}
              onCopy={() => void copy(account.password, "password")}
            />
          </dl>

          <Button
            size="sm"
            variant="secondary"
            className="mt-3"
            disabled={disabled}
            onClick={() => onUse(account)}
          >
            Use demo account
          </Button>
        </div>
      </div>
    </div>
  );
}

function Row({
  term,
  value,
  copied,
  onCopy,
}) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <dt className="w-16 shrink-0 text-ink-muted">{term}</dt>
      <dd className="min-w-0 flex-1 truncate font-mono text-ink" title={value}>
        {value}
      </dd>
      <button
        type="button"
        onClick={onCopy}
        aria-label={`Copy demo ${term.toLowerCase()}`}
        className="shrink-0 rounded-sm px-1.5 py-0.5 font-medium text-accent transition-colors hover:underline"
      >
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  );
}
