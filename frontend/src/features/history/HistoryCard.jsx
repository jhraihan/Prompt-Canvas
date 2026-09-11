import { useState } from "react";

import { Button, IconButton } from "../../components/ui/Button";
import {
  CheckIcon,
  DownloadIcon,
  ExpandIcon,
  LinkIcon,
  RefreshIcon,
  TrashIcon,
} from "../../components/ui/Icons";
import { useToast } from "../../components/ui/Toast";
import { downloadImage } from "../../lib/download";
import { formatRelative, formatSize } from "../../lib/format";

export function HistoryCard({
  image,
  onPreview,
  onDelete,
  onRegenerate,
  onShare,
  selecting = false,
  selected = false,
  onToggleSelected,
}) {
  const { notify } = useToast();
  const [downloading, setDownloading] = useState(false);
  const [failed, setFailed] = useState(false);

  async function onDownload() {
    setDownloading(true);
    try {
      await downloadImage(image.image_url, image.download_filename);
      notify("Image downloaded.");
    } catch {
      notify("Could not download that image.", "info");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <article
      className={[
        "group pc-lift flex flex-col overflow-hidden rounded-2xl border bg-surface shadow-md",
        "transition-colors duration-[200ms] ease-pc",
        selected ? "border-accent shadow-glow" : "border-line hover:border-accent/50",
      ].join(" ")}
    >
      <div
        className="pc-alpha-grid relative bg-inset"
        style={{ aspectRatio: image.size.replace("x", " / ") }}
      >
        {failed ? (
          <div className="flex h-full items-center justify-center px-4 text-center text-sm text-ink-muted">
            This image is no longer available.
          </div>
        ) : (
          <img
            src={image.image_url}
            alt={`Generated image: ${image.prompt}`}
            width={image.width}
            height={image.height}

            loading="lazy"
            decoding="async"
            onError={() => setFailed(true)}
            className="h-full w-full object-cover"
          />
        )}

        {selecting && (
          <button
            type="button"
            role="checkbox"
            aria-checked={selected}
            aria-label={`Select image: ${image.prompt}`}
            onClick={() => onToggleSelected(image)}
            className="absolute inset-0 flex items-start justify-end p-2"
          >
            <span
              className={[
                "flex h-6 w-6 items-center justify-center rounded-md border",
                selected
                  ? "border-accent bg-accent text-accent-fg"
                  : "border-line-strong bg-surface/90 text-transparent",
              ].join(" ")}
            >
              <CheckIcon size={14} />
            </span>
          </button>
        )}

        {!failed && !selecting && (
          <div className="absolute right-2 top-2 opacity-0 transition-opacity duration-[120ms] ease-pc group-hover:opacity-100 group-focus-within:opacity-100">
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
      </div>

      <div className="flex flex-1 flex-col gap-3 p-3.5">
        <div className="min-w-0 flex-1">
          <p className="line-clamp-3 text-sm leading-relaxed text-ink" title={image.prompt}>
            {image.prompt}
          </p>
          <p className="mt-1.5 text-xs text-ink-muted">
            {formatSize(image.size)} - {formatRelative(image.created_at)}
          </p>
        </div>

        <div className={`flex items-center gap-1.5 ${selecting ? "hidden" : ""}`}>
          <Button
            size="sm"
            variant="secondary"
            onClick={() => void onDownload()}
            loading={downloading}
            loadingLabel="..."
            icon={<DownloadIcon size={15} />}
            disabled={failed}
          >
            Download
          </Button>
          <IconButton
            label="Generate again with this prompt"
            size="sm"
            onClick={() => onRegenerate(image)}
          >
            <RefreshIcon size={15} />
          </IconButton>
          <IconButton
            label="Share this image with a link"
            size="sm"
            onClick={() => onShare(image)}
          >
            <LinkIcon size={15} />
          </IconButton>
          <IconButton
            label="Delete this image"
            size="sm"
            variant="danger"
            className="ml-auto"
            onClick={() => onDelete(image)}
          >
            <TrashIcon size={15} />
          </IconButton>
        </div>
      </div>
    </article>
  );
}
