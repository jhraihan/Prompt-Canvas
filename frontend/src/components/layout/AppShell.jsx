import { VerifyEmailBanner } from "../../features/auth/VerifyEmailBanner";
import { Header } from "./Header";

export function AppShell({ children }) {
  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <a href="#main" className="pc-skip-link">
        Skip to main content
      </a>
      <Header />
      <VerifyEmailBanner />
      <main
        id="main"
        tabIndex={-1}
        className="mx-auto w-full max-w-[var(--pc-shell-max)] flex-1 px-4 py-6 outline-none sm:px-6 sm:py-8"
      >
        {children}
      </main>
      <footer className="border-t border-line px-4 py-5 sm:px-6">
        <div className="mx-auto flex max-w-[var(--pc-shell-max)] flex-wrap items-center justify-between gap-2 text-xs text-ink-muted">
          <span>Prompt Canvas - images generated from your prompts.</span>
          <span>Generated images are stored in your private history.</span>
        </div>
      </footer>
    </div>
  );
}
