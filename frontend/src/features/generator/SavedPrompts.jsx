import { useCallback, useEffect, useRef, useState } from "react";

import { Button, IconButton } from "../../components/ui/Button";
import { BookmarkIcon, TrashIcon } from "../../components/ui/Icons";
import { Spinner } from "../../components/ui/Spinner";
import { useToast } from "../../components/ui/Toast";
import { api } from "../../lib/api";

export function SavedPrompts({ currentPrompt, size, quality, onUse, refreshKey }) {
  const { notify } = useToast();
  const [open, setOpen] = useState(false);
  const [prompts, setPrompts] = useState(null);
  const [busy, setBusy] = useState(false);

  const notifyRef = useRef(notify);
  useEffect(() => {
    notifyRef.current = notify;
  }, [notify]);

  const load = useCallback(async () => {
    try {
      setPrompts(await api.savedPrompts());
    } catch {

      setPrompts([]);
    }
  }, []);

  useEffect(() => {

    // oxlint-disable-next-line react/set-state-in-effect
    if (open && prompts === null) void load();
  }, [open, prompts, load]);

  useEffect(() => {
    // oxlint-disable-next-line react/set-state-in-effect
    if (open && refreshKey > 0) void load();
  }, [refreshKey, open, load]);

  const trimmed = currentPrompt.trim();
  const alreadySaved =
    prompts !== null && prompts.some((entry) => entry.prompt === trimmed);
  const canSave = trimmed.length >= 3 && !alreadySaved && !busy;

  async function save() {
    setBusy(true);
    try {
      const created = await api.savePrompt({ prompt: trimmed, size, quality });
      setPrompts((current) => [created, ...(current ?? [])]);
      setOpen(true);
      notifyRef.current("Prompt saved.");
    } catch (error) {
      notifyRef.current(
        error?.fieldError?.("prompt") ?? "Could not save that prompt.",
        "info",
      );
    } finally {
      setBusy(false);
    }
  }

  async function remove(entry) {
    setPrompts((current) => current.filter((item) => item.id !== entry.id));
    try {
      await api.deleteSavedPrompt(entry.id);
    } catch {

      setPrompts((current) => [entry, ...current]);
      notifyRef.current("Could not delete that prompt.", "info");
    }
  }

  function use(entry) {
    onUse(entry);

    void api.useSavedPrompt(entry.id).catch(() => {});
  }

  const count = prompts?.length ?? 0;

  return (
    <div className="rounded-lg border border-line bg-inset">
      <div className="flex items-center gap-2 px-3.5 py-2.5">
        <button
          type="button"
          onClick={() => setOpen((current) => !current)}
          aria-expanded={open}
          className="flex flex-1 items-center gap-2 rounded-sm text-left"
        >
          <BookmarkIcon size={15} className="shrink-0 text-ink-muted" />
          <span className="text-sm font-medium text-ink">Saved prompts</span>
          {count > 0 && (
            <span className="text-xs tabular-nums text-ink-muted">{count}</span>
          )}
        </button>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => void save()}
          disabled={!canSave}
          title={
            alreadySaved
              ? "This prompt is already saved"
              : "Save the current prompt for later"
          }
        >
          {alreadySaved ? "Saved" : "Save"}
        </Button>
      </div>

      {open && (
        <div className="border-t border-line px-3.5 py-3">
          {prompts === null ? (
            <div className="flex justify-center py-2">
              <Spinner size={16} label="Loading saved prompts" />
            </div>
          ) : count === 0 ? (
            <p className="text-sm text-ink-muted">
              Nothing saved yet. Write a prompt you like and select Save.
            </p>
          ) : (
            <ul className="flex list-none flex-col gap-1.5 p-0">
              {prompts.map((entry) => (
                <li key={entry.id} className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => use(entry)}
                    title={entry.prompt}
                    className="min-w-0 flex-1 truncate rounded-sm px-2 py-1.5 text-left text-sm text-ink-secondary transition-colors hover:bg-raised hover:text-ink"
                  >
                    {entry.display_label}
                  </button>
                  <IconButton
                    label={`Delete saved prompt: ${entry.display_label}`}
                    size="sm"
                    variant="ghost"
                    onClick={() => void remove(entry)}
                  >
                    <TrashIcon size={14} />
                  </IconButton>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
