import { useState } from "react";

import { Alert } from "../../components/ui/Alert";
import { Button, IconButton } from "../../components/ui/Button";
import { EmptyState } from "../../components/ui/EmptyState";
import {
  DownloadIcon,
  ExpandIcon,
  ImageIcon,
  RefreshIcon,
} from "../../components/ui/Icons";
import { Spinner } from "../../components/ui/Spinner";
import { downloadImage } from "../../lib/download";
import { formatBytes, formatDate, formatSize } from "../../lib/format";
import { useToast } from "../../components/ui/Toast";

function aspectFor(size) {
  const [width, height] = size.split("x");
  return `${width} / ${height}`;
}

export function ResultPanel({
  status,
  image,
  error,
  pendingSize,
  onRetry,
  onDismissError,
  onPreview,
}) {
  const { notify } = useToast();
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState(null);

  const aspect = aspectFor(image && status !== "generating" ? image.size : pendingSize);

  async function onDownload() {
    if (!image) return;
    setDownloading(true);
    setDownloadError(null);
    try {
      await downloadImage(image.image_url, image.download_filename);
      notify("Image downloaded.");
    } catch {
      setDownloadError("Could not download the image. Please try again.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <section aria-labelledby="result-heading" className="pc-reveal pc-reveal-3 flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <h2 id="result-heading" className="flex items-center gap-2.5 text-lg font-semibold text-ink">
          {status === "generating" && (
            <span aria-hidden="true" className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent opacity-70" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-accent" />
            </span>
          )}
          Result
        </h2>
        {image && status === "success" && (
          <span className="text-sm text-ink-muted">{formatDate(image.created_at)}</span>
        )}
      </div>

      <div
        className={[
          "pc-bloom relative isolate overflow-hidden rounded-2xl shadow-lg",
          image ? "pc-glow-panel" : "border border-line bg-inset",
        ].join(" ")}
        style={{ aspectRatio: aspect }}
        aria-live="polite"
        aria-busy={status === "generating"}
      >
        {status === "generating" && <GeneratingOverlay hasPrevious={Boolean(image)} />}

        {image ? (
          <>
            <img
              src={image.image_url}
              alt={`Generated image: ${image.prompt}`}
              width={image.width}
              height={image.height}
              className={[
                "h-full w-full object-contain transition-opacity duration-[360ms] ease-pc",
                status === "generating" ? "opacity-25" : "opacity-100",
              ].join(" ")}
            />
            {status !== "generating" && (
              <div className="absolute right-3 top-3">
                <IconButton
                  label="View full size"
                  variant="secondary"
                  size="sm"
                  onClick={() => onPreview(image)}
                >
                  <ExpandIcon size={15} />
                </IconButton>
              </div>
            )}
          </>
        ) : status !== "generating" ? (
          <EmptyState
            className="h-full"
            icon={<ImageIcon size={20} />}
            title="Your generated image will appear here"
            description="Describe an image on the left, choose a size, and select Generate image."
          />
        ) : null}
      </div>

      {status === "error" && error && (
        <Alert
          tone="error"
          title="Could not generate the image."
          action={
            <div className="flex gap-2">
              <Button size="sm" variant="secondary" onClick={onRetry} icon={<RefreshIcon size={15} />}>
                Try again
              </Button>
              <Button size="sm" variant="ghost" onClick={onDismissError}>
                Dismiss
              </Button>
            </div>
          }
        >
          {error.message}
        </Alert>
      )}

      {image && status === "success" && (
        <>
          <dl className="flex flex-wrap gap-2">
            <Detail term="Size" value={formatSize(image.size)} tone="text-accent" ring="bg-accent-soft" />
            <Detail
              term="Quality"
              value={image.quality === "hd" ? "High detail" : "Standard"}
              tone="text-plum"
              ring="bg-plum-soft"
            />
            <Detail
              term="Model"
              value={image.model.split("/").pop() ?? image.model}
              tone="text-violet"
              ring="bg-violet-soft"
            />
            <Detail
              term="File"
              value={formatBytes(image.byte_size) || "PNG"}
              tone="text-teal"
              ring="bg-teal-soft"
            />
          </dl>

          <div className="rounded-xl border border-line bg-surface px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.04em] text-ink-muted">
              Prompt
            </p>
            <p className="mt-1.5 text-sm leading-relaxed text-ink">{image.prompt}</p>
          </div>

          {downloadError && <Alert tone="error">{downloadError}</Alert>}

          <div className="flex flex-wrap gap-2">
            <Button
              variant="secondary"
              onClick={() => void onDownload()}
              loading={downloading}
              loadingLabel="Preparing..."
              icon={<DownloadIcon size={16} />}
            >
              Download
            </Button>
            <Button variant="ghost" onClick={onRetry} icon={<RefreshIcon size={16} />}>
              Regenerate
            </Button>
          </div>
        </>
      )}
    </section>
  );
}

function Detail({ term, value, tone, ring }) {
  return (
    <div
      className={`flex min-w-0 items-baseline gap-2 rounded-full ${ring} px-3.5 py-1.5`}
    >
      <dt className={`text-xs font-semibold uppercase tracking-[0.04em] ${tone}`}>
        {term}
      </dt>
      <dd className="truncate text-sm font-medium text-ink" title={value}>
        {value}
      </dd>
    </div>
  );
}

function GeneratingOverlay({ hasPrevious }) {
  return (
    <div
      className={[
        "pc-sweep absolute inset-0 z-10 flex flex-col items-center justify-center gap-4",
        hasPrevious ? "bg-inset/80 backdrop-blur-[3px]" : "bg-inset",
      ].join(" ")}
    >
      <span className="relative z-10 flex h-16 w-16 items-center justify-center rounded-2xl bg-accent-soft text-accent">
        <Spinner size={26} label={null} />
      </span>
      <div className="relative z-10 text-center">
        <p className="text-base font-semibold text-ink">Generating image</p>
        <p className="mt-1 text-sm text-ink-secondary">
          Creating your visual. This usually takes a few seconds.
        </p>
      </div>
    </div>
  );
}
