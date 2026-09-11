import { NavLink } from "react-router-dom";

import { useAuth } from "../../lib/auth";
import { Button } from "../ui/Button";
import { HistoryIcon, LogoutIcon, SparkIcon } from "../ui/Icons";
import { ThemeToggle } from "./ThemeToggle";

const navLink =
  "flex items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm font-medium " +
  "transition-colors duration-[120ms] ease-pc";

export function Header() {
  const { user, isAuthenticated, logout } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-canvas/85 backdrop-blur-md">
      <div className="mx-auto flex h-[var(--pc-header-height)] max-w-[var(--pc-shell-max)] items-center gap-3 px-4 sm:px-6">
        <NavLink
          to="/"
          className="flex items-center gap-2 rounded-md text-ink transition-opacity hover:opacity-80"
        >
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-accent-fg">
            <SparkIcon size={16} />
          </span>
          <span className="text-base font-semibold tracking-[-0.01em]">Prompt Canvas</span>
        </NavLink>

        {isAuthenticated && (
          <nav aria-label="Main" className="ml-2 flex items-center gap-1">
            <NavLink
              to="/"
              end
              aria-label="Generate"
              className={({ isActive }) =>
                `${navLink} ${isActive ? "bg-raised text-ink" : "text-ink-secondary hover:bg-raised hover:text-ink"}`
              }
            >
              <SparkIcon size={15} />
                            <span className="hidden sm:inline">Generate</span>
            </NavLink>
            <NavLink
              to="/history"
              aria-label="History"
              className={({ isActive }) =>
                `${navLink} ${isActive ? "bg-raised text-ink" : "text-ink-secondary hover:bg-raised hover:text-ink"}`
              }
            >
              <HistoryIcon size={15} />
              <span className="hidden sm:inline">History</span>
            </NavLink>
          </nav>
        )}

        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          {isAuthenticated && (
            <>
              <span
                className="hidden max-w-40 truncate text-sm text-ink-secondary md:inline"
                title={user?.email}
              >
                {user?.display_name || user?.email}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => void logout()}
                icon={<LogoutIcon size={15} />}
              >
                <span className="hidden sm:inline">Sign out</span>
                <span className="sm:hidden sr-only">Sign out</span>
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
