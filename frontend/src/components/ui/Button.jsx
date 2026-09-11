import { Spinner } from "./Spinner";

const base =
  "relative inline-flex items-center justify-center gap-2 rounded-md font-semibold " +
  "whitespace-nowrap select-none transition-[background-color,border-color,color,box-shadow,transform] " +
  "duration-[120ms] ease-pc active:translate-y-px " +
  "disabled:cursor-not-allowed disabled:opacity-45 disabled:active:translate-y-0";

const variants = {
  primary:
    "bg-accent text-accent-fg shadow-sm " +
    "hover:not-disabled:bg-accent-hover active:not-disabled:bg-accent-active",
  secondary:
    "bg-raised text-ink border border-line " +
    "hover:not-disabled:border-line-strong hover:not-disabled:bg-inset " +
    "active:not-disabled:bg-inset",
  ghost:
    "bg-transparent text-ink-secondary " +
    "hover:not-disabled:bg-raised hover:not-disabled:text-ink " +
    "active:not-disabled:bg-inset",
  danger:
    "bg-transparent text-danger border border-line " +
    "hover:not-disabled:border-danger hover:not-disabled:bg-danger-soft " +
    "hover:not-disabled:text-danger-hover",
};

const sizes = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-base",
  lg: "h-12 px-6 text-base",
};

export function Button({
  variant = "secondary",
  size = "md",
  loading = false,
  loadingLabel,
  fullWidth = false,
  icon,
  iconEnd,
  disabled,
  children,
  className = "",
  type = "button",
  ...props
}) {
  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      disabled={isDisabled}
      aria-busy={loading || undefined}
      className={[
        base,
        variants[variant],
        sizes[size],
        fullWidth ? "w-full" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...props}
    >
      {loading ? <Spinner size={size === "sm" ? 14 : 16} label={null} /> : icon}
      <span>{loading && loadingLabel ? loadingLabel : children}</span>
      {!loading && iconEnd}
    </button>
  );
}

export function IconButton({
  label,
  variant = "ghost",
  size = "md",
  className = "",
  children,
  type = "button",
  ...props
}) {
  const box = size === "sm" ? "h-8 w-8" : size === "lg" ? "h-12 w-12" : "h-10 w-10";
  return (
    <button
      type={type}
      aria-label={label}
      title={label}
      className={[base, variants[variant], box, "px-0", className].filter(Boolean).join(" ")}
      {...props}
    >
      {children}
    </button>
  );
}
