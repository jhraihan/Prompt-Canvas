import { useTheme } from "../../lib/theme";
import { MonitorIcon, MoonIcon, SunIcon } from "../ui/Icons";

const CHOICES = [
  { value: "light", label: "Light", Icon: SunIcon },
  { value: "dark", label: "Dark", Icon: MoonIcon },
  { value: "system", label: "System", Icon: MonitorIcon },
];

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div
      role="radiogroup"
      aria-label="Colour theme"
      className="flex items-center gap-0.5 rounded-md border border-line bg-inset p-0.5"
    >
      {CHOICES.map(({ value, label, Icon }) => {
        const selected = theme === value;
        return (
          <button
            key={value}
            type="button"
            role="radio"
            aria-checked={selected}
            aria-label={label}
            title={`${label} theme`}
            onClick={() => setTheme(value)}
            className={[
              "flex h-7 w-7 items-center justify-center rounded-sm transition-colors duration-[120ms] ease-pc",
              selected
                ? "bg-raised text-ink shadow-sm"
                : "text-ink-muted hover:text-ink-secondary",
            ].join(" ")}
          >
            <Icon size={15} />
          </button>
        );
      })}
    </div>
  );
}
