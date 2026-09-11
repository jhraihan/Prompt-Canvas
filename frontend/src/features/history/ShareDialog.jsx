import { useCallback, useEffect, useRef, useState } from "react";

import { Alert } from "../../components/ui/Alert";
import { Button, IconButton } from "../../components/ui/Button";
import { Dialog } from "../../components/ui/Dialog";
import { CopyIcon, TrashIcon } from "../../components/ui/Icons";
import { SegmentedControl } from "../../components/ui/SegmentedControl";
import { Spinner } from "../../components/ui/Spinner";
import { useToast } from "../../components/ui/Toast";
import { api } from "../../lib/api";
import { formatDate } from "../../lib/format";

const DURATIONS = [
  { value: "24", label: "1 day" },
  { value: "168", label: "1 week" },
  { value: "720", label: "30 days" },
];

export function ShareDialog({ image, onClose }) {
  const { notify } = useToast();
  const [links, setLinks] = useState(null);
  const [hours, setHours] = useState("168");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);

  const notifyRef = useRef(notify);
  useEffect(() => {
    notifyRef.current = notify;
  }, [notify]);

  const load = useCallback(async (imageId) => {
    try {
      setLinks(await api.shareLinks(imageId));
    } catch {
      setLinks([]);
    }
  }, []);

  useEffect(() => {
    if (!image) return;

    // oxlint-disable-next-line react/set-state-in-effect
    void load(image.id);
  }, [image, load]);

  async function create() {
    if (!image) return;
    setCreating(true);
    setError(null);
    try {
      const link = await api.createShareLink(image.id, Number(hours));
      setLinks((current) => [link, ...(current ?? [])]);
      await copy(link.url, { quiet: true });
      notifyRef.current("Share link created and copied.");
    } catch {
      setError("Could not create a share link. Please try again.");
    } finally {
      setCreating(false);
    }
  }

  async function revoke(link) {
    setLinks((current) =>
      current.map((item) =>
        item.id === link.id ? { ...item, active: false } : item,
      ),
    );
    try {
      await api.revokeShareLink(link.id);
      notifyRef.current("Share link revoked.");
    } catch {
      setLinks((current) =>
        current.map((item) =>
          item.id === link.id ? { ...item, active: true } : item,
        ),
      );
      notifyRef.current("Could not revoke that link.", "info");
    }
  }

  async function copy(url, { quiet = false } = {}) {
    try {
      await navigator.clipboard.writeText(url);
      if (!quiet) notifyRef.current("Link copied.");
    } catch {

      if (!quiet) notifyRef.current("Copy the link from the field above.", "info");
    }
  }

  const active = (links ?? []).filter((link) => link.active);

  return (
    <Dialog
      open={Boolean(image)}
      onClose={onClose}
      title="Share this image"
      description="Anyone with the link can view it, without an account."
      footer={
        <Button variant="ghost" onClick={onClose}>
          Done
        </Button>
      }
    >
      <div className="flex flex-col gap-4">
        <Alert tone="info">
          A share link expires and can be revoked. The image's own file URL
          cannot be — treat it as permanent once it leaves your hands.
        </Alert>

        <div className="flex flex-col gap-1.5">
          <span className="text-sm font-medium text-ink">Link lasts for</span>
          <SegmentedControl
            legend="Link lifetime"
            value={hours}
            onChange={setHours}
            options={DURATIONS}
            disabled={creating}
          />
        </div>

        <Button
          variant="primary"
          onClick={() => void create()}
          loading={creating}
          loadingLabel="Creating..."
        >
          Create share link
        </Button>

        {error && <Alert tone="error">{error}</Alert>}

        {links === null ? (
          <div className="flex justify-center py-2">
            <Spinner size={18} label="Loading share links" />
          </div>
        ) : active.length > 0 ? (
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-ink">
              Active links ({active.length})
            </span>
            <ul className="flex list-none flex-col gap-2 p-0">
              {active.map((link) => (
                <li
                  key={link.id}
                  className="flex items-center gap-2 rounded-lg border border-line bg-inset px-3 py-2"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-mono text-xs text-ink" title={link.url}>
                      {link.url}
                    </p>
                    <p className="mt-0.5 text-xs text-ink-muted">
                      Expires {formatDate(link.expires_at)} · {link.view_count} view
                      {link.view_count === 1 ? "" : "s"}
                    </p>
                  </div>
                  <IconButton
                    label="Copy this link"
                    size="sm"
                    onClick={() => void copy(link.url)}
                  >
                    <CopyIcon size={14} />
                  </IconButton>
                  <IconButton
                    label="Revoke this link"
                    size="sm"
                    variant="danger"
                    onClick={() => void revoke(link)}
                  >
                    <TrashIcon size={14} />
                  </IconButton>
                </li>
              ))}
            </ul>
          </div>
        ) : (
          <p className="text-sm text-ink-muted">
            No active links. Creating one copies it to your clipboard.
          </p>
        )}
      </div>
    </Dialog>
  );
}
