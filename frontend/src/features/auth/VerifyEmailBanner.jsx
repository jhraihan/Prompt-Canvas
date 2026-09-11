import { useState } from "react";

import { Button } from "../../components/ui/Button";
import { CloseIcon, InfoIcon } from "../../components/ui/Icons";
import { useToast } from "../../components/ui/Toast";
import { api } from "../../lib/api";
import { useAuth } from "../../lib/auth";

const DISMISS_KEY = "pc-verify-banner-dismissed";

function readDismissed() {
  try {
    return window.sessionStorage.getItem(DISMISS_KEY) === "1";
  } catch {
    return false;
  }
}

export function VerifyEmailBanner() {
  const { user } = useAuth();
  const { notify } = useToast();
  const [dismissed, setDismissed] = useState(readDismissed);
  const [sending, setSending] = useState(false);

  if (!user || user.email_verified !== false || dismissed) return null;

  async function resend() {
    setSending(true);
    try {
      await api.resendVerification();
      notify("Confirmation email sent. Check your inbox.");
    } catch {
      notify("Could not send that email. Please try again shortly.", "info");
    } finally {
      setSending(false);
    }
  }

  function dismiss() {
    setDismissed(true);
    try {
      window.sessionStorage.setItem(DISMISS_KEY, "1");
    } catch {

    }
  }

  return (
    <div className="border-b border-line bg-inset">
      <div className="mx-auto flex max-w-[var(--pc-shell-max)] flex-wrap items-center gap-3 px-4 py-2.5 sm:px-6">
        <InfoIcon size={16} className="shrink-0 text-ink-muted" />
        <p className="min-w-0 flex-1 text-sm text-ink-secondary">
          <span className="font-medium text-ink">Confirm your email address.</span>{" "}
          Without it there is no way to reset your password if you forget it.
        </p>
        <div className="flex shrink-0 items-center gap-1.5">
          <Button
            size="sm"
            variant="secondary"
            onClick={() => void resend()}
            loading={sending}
            loadingLabel="Sending..."
          >
            Resend email
          </Button>
          <button
            type="button"
            onClick={dismiss}
            aria-label="Dismiss this reminder"
            className="rounded-sm p-1.5 text-ink-muted transition-colors hover:text-ink"
          >
            <CloseIcon size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
