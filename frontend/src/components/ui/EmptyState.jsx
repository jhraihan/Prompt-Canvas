export function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
}) {
  return (
    <div
      className={`flex flex-col items-center justify-center gap-3 px-6 py-12 text-center ${className}`}
    >
      {icon && (
        <div className="flex h-12 w-12 items-center justify-center rounded-full border border-line bg-inset text-ink-muted">
          {icon}
        </div>
      )}
      <div className="max-w-sm">
        <p className="text-base font-semibold text-ink">{title}</p>
        {description && <p className="mt-1.5 text-sm text-ink-secondary">{description}</p>}
      </div>
      {action}
    </div>
  );
}
