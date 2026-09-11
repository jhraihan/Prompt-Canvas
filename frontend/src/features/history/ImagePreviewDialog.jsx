import { useState } from "react";

import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Dialog } from "../../components/ui/Dialog";
import { DownloadIcon } from "../../components/ui/Icons";
import { useToast } from "../../components/ui/Toast";
import { downloadImage } from "../../lib/download";
import { formatDate, formatSize } from "../../lib/format";

export function ImagePreviewDialog({ image, onClose }) {
  const { notify } = useToast();
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);

  async function onDownload() {
    if (!image) return;
    setDownloading(true);
    setError(null);
    try {
      await downloadImage(image.image_url, image.download_filename);
      notify("Image downloaded.");
    } catch {
      setError("Could not download the image. Please try again.");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <Dialog
      open={Boolean(image)}
      onClose={onClose}
      title="Generated image"
      size="lg"
      description={image ? formatDate(image.created_at) : undefined}
      footer={
        image ? (
          <>
            <Button variant="ghost" onClick={onClose}>
              Close
            </Button>
            <Button
              variant="secondary"
              onClick={() => void onDownload()}
              loading={downloading}
              loadingLabel="Preparing..."
              icon={<DownloadIcon size={16} />}
            >
              Download
            </Button>
          </>
        ) : null
      }
    >
      {image && (
        <div className="flex flex-col gap-4">
          <div className="pc-alpha-grid overflow-hidden rounded-lg border border-line">
            <img
              src={image.image_url}
              alt={`Generated image: ${image.prompt}`}
              width={image.width}
              height={image.height}
              className="mx-auto max-h-[60vh] w-auto object-contain"
            />
          </div>
          <div>
            <p className="text-sm leading-relaxed text-ink">{image.prompt}</p>
            <p className="mt-2 text-sm text-ink-muted">
              {formatSize(image.size)} - {image.quality === "hd" ? "High detail" : "Standard"} -{" "}
              {image.model.split("/").pop()}
            </p>
          </div>
          {error && <Alert tone="error">{error}</Alert>}
        </div>
      )}
    </Dialog>
  );
}
