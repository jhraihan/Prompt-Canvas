import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { Alert } from "../../components/ui/Alert";
import { Button } from "../../components/ui/Button";
import { Field } from "../../components/ui/Field";
import { TextInput } from "../../components/ui/TextInput";
import { ApiError } from "../../lib/api";
import { useAuth } from "../../lib/auth";
import { getDemoAccount } from "../../lib/demo";
import { AuthLayout } from "./AuthLayout";
import { DemoAccountCard } from "./DemoAccountCard";

export function LoginPage() {
  const { login, status } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const demoAccount = getDemoAccount();

  if (status === "authenticated") {
    const from = location.state?.from ?? "/";
    return <Navigate to={from} replace />;
  }

  async function signIn(withEmail, withPassword) {
    setError(null);
    setSubmitting(true);
    try {
      await login(withEmail.trim(), withPassword);
      const from = location.state?.from ?? "/";
      navigate(from, { replace: true });
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

  function onSubmit(event) {
    event.preventDefault();
    void signIn(email, password);
  }

  function useDemoAccount(account) {
    setEmail(account.email);
    setPassword(account.password);
    void signIn(account.email, account.password);
  }

  const formError =
    error && error.status === 401
      ? "That email and password do not match an account."
      : error && Object.keys(error.fieldErrors).length === 0
        ? error.message
        : null;

  return (
    <AuthLayout
      title="Sign in"
      subtitle="Pick up where you left off, with your full generation history."
      footer={
        <>
          New to Prompt Canvas?{" "}
          <Link to="/register" className="font-medium text-accent hover:underline">
            Create an account
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} noValidate aria-label="Sign in" className="flex flex-col gap-4">
        {formError && <Alert tone="error">{formError}</Alert>}

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

        <Field
          label="Password"
          error={error?.fieldError("password")}
          required
          adornment={
            <Link
              to="/forgot-password"
              className="text-sm font-medium text-accent hover:underline"
            >
              Forgot?
            </Link>
          }
        >
          {({ id, describedBy, invalid }) => (
            <TextInput
              id={id}
              aria-describedby={describedBy}
              invalid={invalid}
              type="password"
              name="password"
              autoComplete="current-password"
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
          loadingLabel="Signing in..."
          disabled={!email.trim() || !password}
        >
          Sign in
        </Button>
      </form>

      {demoAccount && (
        <div className="mt-4">
          <DemoAccountCard
            account={demoAccount}
            onUse={useDemoAccount}
            disabled={submitting}
          />
        </div>
      )}
    </AuthLayout>
  );
}
