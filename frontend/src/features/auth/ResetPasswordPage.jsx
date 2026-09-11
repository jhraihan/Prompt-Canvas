import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { TextInput } from "../../components/ui/TextInput";
import { ApiError, api, setAccessToken } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AuthLayout } from "./AuthLayout";

const MIN_PASSWORD = 8;

export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const navigate = useNavigate();
  const { setUser } = useAuth();

  const uid = params.get("uid");
  const token = params.get("token");

  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  if (!uid || !token) {
    return (
      <AuthLayout
        title="This link is incomplete"
        subtitle="The reset link looks malformed or was cut short by your email client."
        footer={
          <Link to="/forgot-password" className="font-medium text-accent hover:underline">
            Request a new link
          </Link>
        }
      >
        <Alert tone="error">
          Copy the whole link from the email, or request a fresh one.
        </Alert>
      </AuthLayout>
    );
  }

  const tooShort = password.length > 0 && password.length < MIN_PASSWORD;
  const mismatch = confirmation.length > 0 && password !== confirmation;
  const canSubmit =
    password.length >= MIN_PASSWORD && password === confirmation && !submitting;

  async function onSubmit(event) {
    event.preventDefault();
    if (!canSubmit) return;
    setError(null);
    setSubmitting(true);
    try {
      const result = await api.confirmPasswordReset({
        uid,
        token,
        new_password: password,
      });

      setAccessToken(result.access);
      setUser(result.user);
      navigate("/", { replace: true });
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught
          : new ApiError(0, "error", "Something went wrong. Please try again."),
      );
      setSubmitting(false);
    }
  }

  const linkRejected =
    error && error.status === 400 && !error.fieldError("new_password");

  return (
    <AuthLayout
      title="Choose a new password"
      subtitle="This finishes the reset and signs you in."
      footer={
        <Link to="/login" className="font-medium text-accent hover:underline">
          Back to sign in
        </Link>
      }
    >
      {linkRejected && (
        <Alert
          tone="error"
          title="This link is no longer valid"
          className="mb-4"
          action={
            <Button
              size="sm"
              variant="secondary"
              onClick={() => navigate("/forgot-password")}
            >
              Request a new link
            </Button>
          }
        >
          Reset links expire after an hour and can only be used once.
        </Alert>
      )}

      <form
        onSubmit={onSubmit}
        noValidate
        aria-label="Choose a new password"
        className="flex flex-col gap-4"
      >
        {error && !linkRejected && !error.fieldError("new_password") && (
          <Alert tone="error">{error.message}</Alert>
        )}

        <Field
          label="New password"
          hint={`At least ${MIN_PASSWORD} characters.`}
          error={
            tooShort
              ? `Use at least ${MIN_PASSWORD} characters.`
              : error?.fieldError("new_password")
          }
          required
        >
          {({ id, describedBy, invalid }) => (
            <TextInput
              id={id}
              aria-describedby={describedBy}
              invalid={invalid}
              type="password"
              name="new_password"
              autoComplete="new-password"
              autoFocus
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          )}
        </Field>

        <Field
          label="Confirm new password"
          error={mismatch ? "These passwords do not match." : null}
          required
        >
          {({ id, describedBy, invalid }) => (
            <TextInput
              id={id}
              aria-describedby={describedBy}
              invalid={invalid}
              type="password"
              name="confirm_password"
              autoComplete="new-password"
              required
              value={confirmation}
              onChange={(event) => setConfirmation(event.target.value)}
            />
          )}
        </Field>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          loading={submitting}
          loadingLabel="Saving..."
          disabled={!canSubmit}
        >
          Set new password
        </Button>
      </form>
    </AuthLayout>
  );
}
