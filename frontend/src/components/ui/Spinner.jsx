export function Spinner({ size = 16, className = "", label = "Loading" }) {
  return (
    <span
      className={`inline-flex shrink-0 ${className}`}
      role={label ? "status" : undefined}
      aria-label={label ?? undefined}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        aria-hidden="true"
        style={{ animation: "pc-spin 720ms linear infinite" }}
      >
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.22" strokeWidth="2.5" />
        <path
          d="M21 12a9 9 0 00-9-9"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
      </svg>
    </span>
  );
}
