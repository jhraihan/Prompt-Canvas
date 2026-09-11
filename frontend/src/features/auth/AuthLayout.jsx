import { ThemeToggle } from "../../components/layout/ThemeToggle";
import { SparkIcon } from "../../components/ui/Icons";

export function AuthLayout({ title, subtitle, children, footer }) {
  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <div className="flex items-center justify-between px-4 py-4 sm:px-6">
        <div className="flex items-center gap-2 text-ink">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-accent-fg">
            <SparkIcon size={16} />
          </span>
          <span className="text-base font-semibold tracking-[-0.01em]">Prompt Canvas</span>
        </div>
        <ThemeToggle />
      </div>

      <main className="flex flex-1 items-center justify-center px-4 py-8 sm:px-6">
        <div className="w-full max-w-sm">
          <div className="mb-6">
            <h1 className="text-2xl text-ink">{title}</h1>
            <p className="mt-1.5 text-base text-ink-secondary">{subtitle}</p>
          </div>
          {children}
          <p className="mt-6 text-center text-sm text-ink-secondary">{footer}</p>
        </div>
      </main>
    </div>
  );
}
