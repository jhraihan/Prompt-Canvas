import { useState } from "react";
import { Link } from "react-router-dom";

import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { TextInput } from "../../components/ui/TextInput";
import { ApiError, api } from "../../lib/api";
import { AuthLayout } from "./AuthLayout";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState(null);

  async function onSubmit(event) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.requestPasswordReset(email.trim());
      setSent(true);
    } catch (caught) {

      setError(
        caught instanceof ApiError
          ? caught
          : new ApiError(0, "error", "Something went wrong. Please try again."),
      );
    } finally {
      setSubmitting(false);
    }
  }

  const footer = (
    <>
      Remembered it?{" "}
      <Link to="/login" className="font-medium text-accent hover:underline">
        Back to sign in
      </Link>
    </>
  );

  if (sent) {
    return (
      <AuthLayout
        title="Check your inbox"
        subtitle="If an account exists for that address, a reset link is on its way."
        footer={footer}
      >
        <Alert tone="success" title="Request received">
          The link expires in an hour and can be used once. If nothing arrives
          within a few minutes, check your spam folder.
        </Alert>
        <Button
          variant="ghost"
          fullWidth
          className="mt-4"
          onClick={() => {
            setSent(false);
            setError(null);
          }}
        >
          Use a different address
        </Button>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout
      title="Reset your password"
      subtitle="Enter the address you signed up with and we'll send you a link."
      footer={footer}
    >
      <form
        onSubmit={onSubmit}
        noValidate
        aria-label="Reset your password"
        className="flex flex-col gap-4"
      >
        {error && <Alert tone="error">{error.message}</Alert>}

        <Field label="Email" error={error?.fieldError("email")} required>
          {({ id, describedBy, invalid }) => (
            <TextInput
              id={id}
              aria-describedby={describedBy}
              invalid={invalid}
              type="email"
              name="email"
              autoComplete="email"
              autoFocus
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
          )}
        </Field>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          loading={submitting}
          loadingLabel="Sending..."
          disabled={!email.trim()}
        >
          Send reset link
        </Button>
      </form>
    </AuthLayout>
  );
}
