import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ThemeToggle } from "../components/layout/ThemeToggle";
import { Alert } from "../components/ui/Alert";
import { Button } from "../components/ui/Button";
import { SparkIcon } from "../components/ui/Icons";
import { Spinner } from "../components/ui/Spinner";
import { api } from "../lib/api";
import { formatDate, formatSize } from "../lib/format";

export function SharedImagePage() {
  const { token } = useParams();
  const [state, setState] = useState("loading");
  const [image, setImage] = useState(null);

  useEffect(() => {
    let cancelled = false;
    api
      .sharedImage(token)
      .then((result) => {
        if (cancelled) return;
        setImage(result);
        setState("ready");
      })
      .catch(() => {
        if (!cancelled) setState("unavailable");
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <div className="flex items-center justify-between px-4 py-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2 text-ink">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-accent-fg">
            <SparkIcon size={16} />
          </span>
          <span className="text-base font-semibold tracking-[-0.01em]">
            Prompt Canvas
          </span>
        </Link>
        <ThemeToggle />
      </div>

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-6 sm:px-6">
        {state === "loading" && (
          <div className="flex flex-1 items-center justify-center">
            <Spinner size={22} label="Loading the shared image" />
          </div>
        )}

        {state === "unavailable" && (
          <div className="flex flex-1 flex-col items-center justify-center gap-4 text-center">
            <Alert tone="error" title="This link is not available">
              Share links expire, and the person who created it can revoke it at
              any time.
            </Alert>
            <Button variant="primary" onClick={() => (window.location.href = "/")}>
              Generate your own image
            </Button>
          </div>
        )}

        {state === "ready" && image && (
          <div className="flex flex-col gap-4">
            <div
              className="overflow-hidden rounded-xl border border-line bg-inset"
              style={{ aspectRatio: image.size.replace("x", " / ") }}
            >
              <img
                src={image.image_url}
                alt={`Generated image: ${image.prompt}`}
                width={image.width}
                height={image.height}
                className="h-full w-full object-contain"
              />
            </div>

            <div>
              <p className="text-sm leading-relaxed text-ink">{image.prompt}</p>
              <p className="mt-2 text-sm text-ink-muted">
                {formatSize(image.size)} · {formatDate(image.created_at)}
              </p>
            </div>

            <div className="rounded-lg border border-line bg-surface px-4 py-3">
              <p className="text-sm text-ink-secondary">
                Made with Prompt Canvas — describe an image and it generates one.
              </p>
              <Button
                variant="secondary"
                size="sm"
                className="mt-2.5"
                icon={<SparkIcon size={15} />}
                onClick={() => (window.location.href = "/register")}
              >
                Try it yourself
              </Button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
