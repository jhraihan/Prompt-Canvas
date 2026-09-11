import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { TextInput } from "../../components/ui/TextInput";
import { ApiError } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { AuthLayout } from "./AuthLayout";

const MIN_PASSWORD = 8;

export function RegisterPage() {
  const { register, status } = useAuth();
  const navigate = useNavigate();

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated") return <Navigate to="/" replace />;

  const passwordTooShort = password.length > 0 && password.length < MIN_PASSWORD;

  async function onSubmit(event) {
    event.preventDefault();
    if (passwordTooShort) return;
    setError(null);
    setSubmitting(true);
    try {
      await register({
        email: email.trim(),
        password,
        display_name: displayName.trim(),
      });
      navigate("/", { replace: true });
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

  const formError =
    error && Object.keys(error.fieldErrors).length === 0 ? error.message : null;

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Your generated images stay in a history only you can see."
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-accent hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate className="flex flex-col gap-4">
        {formError && <Alert tone="error">{formError}</Alert>}

        <Field
          label="Name"
          hint="Shown in the header. You can change it later."
          error={error?.fieldError("display_name")}
        >
          {({ id, describedBy, invalid }) => (
            <TextInput
              id={id}
              aria-describedby={describedBy}
              invalid={invalid}
              name="display_name"
              autoComplete="name"
              autoFocus
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              placeholder="Optional"
            />
          )}
        </Field>

        <Field label="Email" error={error?.fieldError("email")} required>
          {({ id, describedBy, invalid }) => (
            <TextInput
              id={id}
              aria-describedby={describedBy}
              invalid={invalid}
              type="email"
              name="email"
              autoComplete="email"
              required
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
          )}
        </Field>

        <Field
          label="Password"
          hint={`At least ${MIN_PASSWORD} characters.`}
          error={
            passwordTooShort
              ? `Use at least ${MIN_PASSWORD} characters.`
              : error?.fieldError("password")
          }
          required
        >
          {({ id, describedBy, invalid }) => (
            <TextInput
              id={id}
              aria-describedby={describedBy}
              invalid={invalid}
              type="password"
              name="password"
              autoComplete="new-password"
              required
              value={password}
              onChange={(event) => setPassword(event.target.value)}
            />
          )}
        </Field>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          fullWidth
          loading={submitting}
          loadingLabel="Creating account..."
          disabled={!email.trim() || password.length < MIN_PASSWORD}
        >
          Create account
        </Button>
      </form>
    </AuthLayout>
  );
}
