import { useId } from "react";

export function SegmentedControl({
  legend,
  name,
  value,
  options,
  onChange,
  disabled = false,
  describedBy,
  columns,
}) {
  const generatedName = useId();
  const groupName = name ?? generatedName;

  return (
    <fieldset
      className="min-w-0 border-0 p-0 m-0"
      disabled={disabled}
      aria-describedby={describedBy}
    >
      <legend className="sr-only">{legend}</legend>
      <div
        className="grid gap-1.5 rounded-lg border border-line bg-inset p-1.5"
        style={{ gridTemplateColumns: `repeat(${columns ?? options.length}, minmax(0, 1fr))` }}
      >
        {options.map((option) => {
          const selected = option.value === value;
          return (
            <label
              key={option.value}
              className={[
                "group relative flex cursor-pointer flex-col items-center justify-center",
                "gap-0.5 rounded-md px-2 py-2 text-center transition-colors",
                "duration-[120ms] ease-pc",
                selected
                  ? "bg-raised text-ink shadow-sm"
                  : "text-ink-secondary hover:bg-raised/60 hover:text-ink",
                disabled ? "cursor-not-allowed opacity-55" : "",
                "has-[:focus-visible]:outline has-[:focus-visible]:outline-2",
                "has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-focus",
              ].join(" ")}
            >
              <input
                type="radio"
                name={groupName}
                value={option.value}
                checked={selected}
                disabled={disabled}
                onChange={() => onChange(option.value)}
                className="sr-only"
              />
              <span className="text-sm font-medium leading-tight">{option.label}</span>
              {option.detail && (
                <span className="text-xs text-ink-muted leading-tight">{option.detail}</span>
              )}
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
