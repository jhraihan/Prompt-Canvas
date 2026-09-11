import { useId } from "react";

function AspectPreview({ size, active }) {
  const [width, height] = size.split("x").map(Number);
  const longest = Math.max(width, height);
  const w = Math.round((width / longest) * 26);
  const h = Math.round((height / longest) * 26);

  return (
    <span
      aria-hidden="true"
      className={[
        "block rounded-[3px] border-2 transition-colors duration-[120ms]",
        active ? "border-accent-fg bg-accent-fg/25" : "border-ink-muted",
      ].join(" ")}
      style={{ width: `${w}px`, height: `${h}px` }}
    />
  );
}

export function SizeCards({ value, onChange, options, disabled }) {
  const name = useId();

  return (
    <fieldset className="min-w-0 border-0 p-0 m-0" disabled={disabled}>
      <legend className="sr-only">Image size</legend>
      <div className="grid grid-cols-3 gap-2">
        {options.map((option) => {
          const active = option.value === value;
          return (
            <label
              key={option.value}
              className={[
                "group relative flex cursor-pointer flex-col items-center gap-2 rounded-xl",
                "border px-2 py-3 text-center transition-all duration-[160ms] ease-pc",
                active
                  ? "pc-chip-active border-transparent"
                  : "border-line bg-raised text-ink-secondary hover:border-accent/50 hover:text-ink",
                disabled ? "cursor-not-allowed opacity-55" : "",
                "has-[:focus-visible]:outline has-[:focus-visible]:outline-2",
                "has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-focus",
              ].join(" ")}
            >
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={active}
                disabled={disabled}
                onChange={() => onChange(option.value)}
                className="sr-only"
              />
              <span className="flex h-7 items-center">
                <AspectPreview size={option.value} active={active} />
              </span>
              <span className="text-sm font-semibold leading-none">{option.label}</span>
              <span
                className={`text-xs leading-none ${active ? "opacity-80" : "text-ink-muted"}`}
              >
                {option.detail}
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}

export function QualityCards({ value, onChange, options, disabled }) {
  const name = useId();

  return (
    <fieldset className="min-w-0 border-0 p-0 m-0" disabled={disabled}>
      <legend className="sr-only">Quality</legend>
      <div className="grid grid-cols-2 gap-2">
        {options.map((option) => {
          const active = option.value === value;
          const isHd = option.value === "hd";
          return (
            <label
              key={option.value}
              className={[
                "group relative flex cursor-pointer items-center gap-2.5 rounded-xl",
                "border px-3.5 py-3 transition-all duration-[160ms] ease-pc",
                active
                  ? "pc-chip-active border-transparent"
                  : "border-line bg-raised text-ink-secondary hover:border-accent/50 hover:text-ink",
                disabled ? "cursor-not-allowed opacity-55" : "",
                "has-[:focus-visible]:outline has-[:focus-visible]:outline-2",
                "has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-focus",
              ].join(" ")}
            >
              <input
                type="radio"
                name={name}
                value={option.value}
                checked={active}
                disabled={disabled}
                onChange={() => onChange(option.value)}
                className="sr-only"
              />
                            <span aria-hidden="true" className="flex items-end gap-[3px]">
                {[0, 1, 2, 3].map((bar) => (
                  <span
                    key={bar}
                    className={[
                      "w-[3px] rounded-full transition-colors duration-[120ms]",
                      active ? "bg-accent-fg" : "bg-ink-muted",
                      bar > 1 && !isHd ? "opacity-25" : "",
                    ].join(" ")}
                    style={{ height: `${6 + bar * 3}px` }}
                  />
                ))}
              </span>
              <span className="min-w-0 text-left">
                <span className="block text-sm font-semibold leading-tight">
                  {option.label}
                </span>
                <span
                  className={`block text-xs leading-tight ${active ? "opacity-80" : "text-ink-muted"}`}
                >
                  {option.detail}
                </span>
              </span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );
}
