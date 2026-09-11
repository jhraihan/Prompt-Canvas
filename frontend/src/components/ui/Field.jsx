import { useId } from "react";

export function Field({
  label,
  hint,
  error,
  adornment,
  required = false,
  children,
}) {
  const id = useId();
  const hintId = `${id}-hint`;
  const errorId = `${id}-error`;
  const describedBy = error ? errorId : hint ? hintId : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="text-sm font-medium text-ink">
          {label}
          {required && (
            <span className="ml-1 text-danger" aria-hidden="true">
              *
            </span>
          )}
        </label>
        {adornment}
      </div>

      {children({ id, describedBy, invalid: Boolean(error) })}

      {error ? (
        <p id={errorId} role="alert" className="text-sm text-danger">
          {error}
        </p>
      ) : hint ? (
        <p id={hintId} className="text-sm text-ink-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

export const controlClasses =
  "w-full rounded-md border bg-raised px-3 text-base text-ink " +
  "placeholder:text-ink-muted transition-colors duration-[120ms] ease-pc " +
  "hover:not-disabled:border-line-strong " +
  "disabled:cursor-not-allowed disabled:opacity-55";

export function controlBorder(invalid) {
  return invalid ? "border-danger" : "border-line";
}
