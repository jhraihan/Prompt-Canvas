import { AlertIcon, CheckIcon, InfoIcon } from "./Icons";

const tones = {
  error: { wrapper: "border-danger/45 bg-danger-soft text-ink", icon: AlertIcon },
  success: { wrapper: "border-success/45 bg-success-soft text-ink", icon: CheckIcon },
  warning: { wrapper: "border-warning/45 bg-warning-soft text-ink", icon: AlertIcon },
  info: { wrapper: "border-line bg-inset text-ink", icon: InfoIcon },
};

const iconColour = {
  error: "text-danger",
  success: "text-success",
  warning: "text-warning",
  info: "text-ink-secondary",
};

export function Alert({ tone = "info", title, children, action, className = "" }) {
  const { wrapper, icon: Glyph } = tones[tone];
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`flex items-start gap-3 rounded-lg border px-3.5 py-3 ${wrapper} ${className}`}
    >
      <Glyph size={18} className={`mt-0.5 shrink-0 ${iconColour[tone]}`} />
      <div className="min-w-0 flex-1">
        {title && <p className="text-sm font-semibold">{title}</p>}
        <div className="text-sm text-ink-secondary">{children}</div>
        {action && <div className="mt-2.5">{action}</div>}
      </div>
    </div>
  );
}
