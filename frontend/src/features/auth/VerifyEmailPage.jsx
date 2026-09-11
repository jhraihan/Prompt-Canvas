import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Spinner } from "../../components/ui/Spinner";
import { ApiError, api } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AuthLayout } from "./AuthLayout";

export function VerifyEmailPage() {
  const [params] = useSearchParams();
  const { user, setUser } = useAuth();

  const uid = params.get("uid");
  const token = params.get("token");

  const [status, setStatus] = useState(uid && token ? "verifying" : "invalid");
  const [message, setMessage] = useState(null);

  const attempted = useRef(false);

  const session = useRef({ user, setUser });
  useEffect(() => {
    session.current = { user, setUser };
  }, [user, setUser]);

  useEffect(() => {
    if (!uid || !token || attempted.current) return;
    attempted.current = true;

    let cancelled = false;
    api
      .verifyEmail({ uid, token })
      .then((result) => {
        if (cancelled) return;
        setStatus("verified");

        const { user: current, setUser: update } = session.current;
        if (result?.user && current) update(result.user);
      })
      .catch((caught) => {
        if (cancelled) return;
        setStatus("failed");
        setMessage(
          caught instanceof ApiError
            ? caught.message
            : "Could not confirm your email. Please try again.",
        );
      });

    return () => {
      cancelled = true;
    };
  }, [uid, token]);

  const footer = (
    <Link to="/" className="font-medium text-accent hover:underline">
      Go to the generator
    </Link>
  );

  if (status === "verifying") {
    return (
      <AuthLayout title="Confirming your email" subtitle="This takes a moment." footer={footer}>
        <div className="flex justify-center py-6">
          <Spinner size={24} label="Confirming your email address" />
        </div>
      </AuthLayout>
    );
  }

  if (status === "verified") {
    return (
      <AuthLayout
        title="Email confirmed"
        subtitle="Thanks — we can now reach you if you ever need to reset your password."
        footer={footer}
      >
        <Alert tone="success" title="You're all set">
          Nothing else to do. Your account was already working; this just makes
          password recovery possible.
        </Alert>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Could not confirm this link"
      subtitle="Confirmation links expire, and each one works only once."
      footer={footer}
    >
      <Alert tone="error">
        {status === "invalid"
          ? "This link is incomplete. Copy the whole link from the email."
          : message}
      </Alert>
      <p className="mt-4 text-sm text-ink-secondary">
        If your address is already confirmed, you can ignore this. Otherwise
        sign in and request a fresh link from the banner at the top of the page.
      </p>
      <Button
        variant="secondary"
        fullWidth
        className="mt-4"
        onClick={() => {
          window.location.href = "/login";
        }}
      >
        Go to sign in
      </Button>
    </AuthLayout>
  );
}
