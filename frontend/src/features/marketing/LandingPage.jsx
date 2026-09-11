import { Link } from "react-router-dom";

import { ThemeToggle } from "../../components/layout/ThemeToggle";
import { Button } from "../../components/ui/Button";
import {
  BookmarkIcon,
  DownloadIcon,
  HistoryIcon,
  ImageIcon,
  LinkIcon,
  SparkIcon,
} from "../../components/ui/Icons";

const STATS = [
  { value: "3", label: "Image sizes" },
  { value: "2", label: "Quality tiers" },
  { value: "<10s", label: "Typical generation" },
];

const FEATURES = [
  {
    icon: SparkIcon,
    tone: "text-accent",
    ring: "bg-accent-soft",
    title: "Describe it, see it",
    body: "Write what you want in plain language. Pick a size and a quality tier, and the image comes back in seconds with everything needed to use it.",
  },
  {
    icon: HistoryIcon,
    tone: "text-plum",
    ring: "bg-plum-soft",
    title: "A private history",
    body: "Every generation is saved with its prompt and settings. Yours alone — another account's images are simply not there.",
  },
  {
    icon: BookmarkIcon,
    tone: "text-violet",
    ring: "bg-violet-soft",
    title: "Keep what works",
    body: "Save a prompt that landed well, with the size and quality it used, and bring the whole setup back in one click.",
  },
  {
    icon: LinkIcon,
    tone: "text-teal",
    ring: "bg-teal-soft",
    title: "Share on your terms",
    body: "Create a link that expires when you say, and revoke it whenever you like. You keep control after it leaves your hands.",
  },
  {
    icon: DownloadIcon,
    tone: "text-sun",
    ring: "bg-sun-soft",
    title: "Download, named properly",
    body: "Files arrive named after the prompt and the moment you made them, not as a string of random characters.",
  },
  {
    icon: ImageIcon,
    tone: "text-accent",
    ring: "bg-accent-soft",
    title: "Yours to leave",
    body: "Delete any image and it goes — the row and the file both. No archive, no soft delete, no quiet copy.",
  },
];

const STEPS = [
  { n: "01", title: "Describe", body: "Subject, setting, lighting, style. The built-in guide shows the recipe." },
  { n: "02", title: "Generate", body: "Choose a size and quality. The result appears beside the form as it arrives." },
  { n: "03", title: "Keep it", body: "Download it, save the prompt, share a link, or run it again with a tweak." },
];

export function LandingPage() {
  return (
    <div className="min-h-dvh bg-canvas">
      <a href="#main" className="pc-skip-link">
        Skip to main content
      </a>

      <header className="sticky top-0 z-40 border-b border-line bg-canvas/80 backdrop-blur-md">
        <div className="mx-auto flex h-[var(--pc-header-height)] max-w-[var(--pc-shell-max)] items-center gap-3 px-4 sm:px-6">
          <span className="flex items-center gap-2 text-ink">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-accent-fg shadow-glow">
              <SparkIcon size={17} />
            </span>
            <span className="text-base font-semibold tracking-[-0.01em]">
              Prompt Canvas
            </span>
          </span>

          <nav aria-label="Page sections" className="ml-6 hidden items-center gap-1 md:flex">
            <a href="#features" className="rounded-md px-3 py-1.5 text-sm font-medium text-ink-secondary transition-colors hover:bg-inset hover:text-ink">
              Features
            </a>
            <a href="#how" className="rounded-md px-3 py-1.5 text-sm font-medium text-ink-secondary transition-colors hover:bg-inset hover:text-ink">
              How it works
            </a>
          </nav>

          <div className="ml-auto flex items-center gap-2">
            <ThemeToggle />
            <Link
              to="/login"
              className="rounded-md px-3 py-1.5 text-sm font-medium text-ink-secondary transition-colors hover:bg-inset hover:text-ink"
            >
              Sign in
            </Link>
            <Link to="/register">
              <Button variant="primary" size="sm">
                Get started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main id="main" tabIndex={-1} className="outline-none">
                <section className="pc-aurora relative">
          <div
            aria-hidden="true"
            className="pc-grid-bg pointer-events-none absolute inset-0 opacity-60"
          />

          <div className="mx-auto max-w-[var(--pc-shell-max)] px-4 pb-20 pt-16 sm:px-6 sm:pb-28 sm:pt-24">
            <p className="pc-reveal pc-reveal-1 mb-5 inline-flex items-center gap-2 rounded-full border border-line bg-surface/80 px-3.5 py-1.5 text-sm text-ink-secondary shadow-sm backdrop-blur">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-70" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
              </span>
              Powered by FLUX.1 — images in seconds
            </p>

            <h1 className="pc-reveal pc-reveal-2 max-w-5xl text-5xl font-bold leading-[0.95] tracking-[-0.035em] text-ink">
              Start creating
              <br />
              <span className="pc-gradient-text">something remarkable</span>
            </h1>

            <p className="pc-reveal pc-reveal-3 mt-6 max-w-[var(--pc-prose-max)] text-lg leading-relaxed text-ink-secondary">
              Describe an image in your own words and watch it arrive. Every
              generation is saved to a private history you can return to,
              refine, download, or share — on your terms.
            </p>

            <div className="pc-reveal pc-reveal-4 mt-8 flex flex-wrap items-center gap-3">
              <Link to="/register">
                <Button variant="primary" size="lg" className="shadow-glow" icon={<SparkIcon size={17} />}>
                  Start creating — free
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="secondary" size="lg">
                  I already have an account
                </Button>
              </Link>
            </div>

            <dl className="pc-reveal pc-reveal-5 mt-14 flex flex-wrap gap-3">
              {STATS.map((stat, index) => (
                <div
                  key={stat.label}
                  className={`pc-float pc-float-${index + 1} rounded-2xl border border-line bg-surface/90 px-5 py-3.5 shadow-md backdrop-blur`}
                >
                  <dt className="sr-only">{stat.label}</dt>
                  <dd>
                    <span className="pc-gradient-text block text-4xl font-bold leading-none tracking-[-0.04em]">
                      {stat.value}
                    </span>
                    <span className="mt-1.5 block text-sm text-ink-muted">
                      {stat.label}
                    </span>
                  </dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

                <section id="features" className="border-t border-line bg-surface">
          <div className="mx-auto max-w-[var(--pc-shell-max)] px-4 py-20 sm:px-6 sm:py-28">
            <h2 className="max-w-3xl text-4xl font-bold tracking-[-0.03em] text-ink">
              Everything around the image, handled
            </h2>
            <p className="mt-4 max-w-[var(--pc-prose-max)] text-lg text-ink-secondary">
              Generating is the easy part. What makes a tool worth returning to
              is what happens afterwards.
            </p>

            <ul className="mt-12 grid list-none grid-cols-1 gap-4 p-0 sm:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map((feature) => (
                <li key={feature.title}>
                  <article className="pc-lift h-full rounded-2xl border border-line bg-canvas p-6 shadow-sm">
                    <span
                      className={`mb-4 flex h-11 w-11 items-center justify-center rounded-xl ${feature.ring} ${feature.tone}`}
                    >
                      <feature.icon size={20} />
                    </span>
                    <h3 className="text-lg font-semibold text-ink">{feature.title}</h3>
                    <p className="mt-2 text-base leading-relaxed text-ink-secondary">
                      {feature.body}
                    </p>
                  </article>
                </li>
              ))}
            </ul>
          </div>
        </section>

                <section id="how" className="border-t border-line">
          <div className="mx-auto max-w-[var(--pc-shell-max)] px-4 py-20 sm:px-6 sm:py-28">
            <h2 className="text-4xl font-bold tracking-[-0.03em] text-ink">
              Three steps, no manual
            </h2>

            <ol className="mt-12 grid list-none grid-cols-1 gap-6 p-0 md:grid-cols-3">
              {STEPS.map((step) => (
                <li key={step.n} className="relative rounded-2xl border border-line bg-surface p-6 shadow-sm">
                  <span className="pc-gradient-text text-4xl font-bold leading-none tracking-[-0.04em]">
                    {step.n}
                  </span>
                  <h3 className="mt-4 text-lg font-semibold text-ink">{step.title}</h3>
                  <p className="mt-2 text-base leading-relaxed text-ink-secondary">
                    {step.body}
                  </p>
                </li>
              ))}
            </ol>
          </div>
        </section>

                <section className="border-t border-line">
          <div className="mx-auto max-w-[var(--pc-shell-max)] px-4 py-20 sm:px-6 sm:py-24">
            <div className="pc-aurora relative overflow-hidden rounded-3xl border border-line bg-surface px-6 py-16 text-center shadow-lg sm:px-12">
              <h2 className="mx-auto max-w-3xl text-4xl font-bold tracking-[-0.03em] text-ink">
                Your first image is a sentence away
              </h2>
              <p className="mx-auto mt-4 max-w-[var(--pc-prose-max)] text-lg text-ink-secondary">
                Free to start. No card, no trial countdown.
              </p>
              <div className="mt-8 flex justify-center">
                <Link to="/register">
                  <Button variant="primary" size="lg" className="shadow-glow" icon={<SparkIcon size={17} />}>
                    Create your account
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line px-4 py-8 sm:px-6">
        <div className="mx-auto flex max-w-[var(--pc-shell-max)] flex-wrap items-center justify-between gap-3 text-sm text-ink-muted">
          <span className="flex items-center gap-2">
            <SparkIcon size={14} />
            Prompt Canvas
          </span>
          <span>Images you generate stay in your private history.</span>
        </div>
      </footer>
    </div>
  );
}
