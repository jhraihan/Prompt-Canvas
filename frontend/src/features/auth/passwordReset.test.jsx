import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, getAccessToken } from "../../lib/api";
import { makeUser, renderWithProviders } from "../../test/utils";
import { ForgotPasswordPage } from "./ForgotPasswordPage";
import { ResetPasswordPage } from "./ResetPasswordPage";
import { VerifyEmailPage } from "./VerifyEmailPage";

beforeEach(() => {
  vi.spyOn(api, "restoreSession").mockResolvedValue(null);
});

describe("requesting a reset link", () => {
  it("keeps the button disabled until an address is entered", () => {
    renderWithProviders(<ForgotPasswordPage />);
    expect(screen.getByRole("button", { name: /send reset link/i })).toBeDisabled();
  });

  it("submits the trimmed address", async () => {
    const user = userEvent.setup();
    const request = vi.spyOn(api, "requestPasswordReset").mockResolvedValue({});
    renderWithProviders(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), "  painter@example.com  ");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    await waitFor(() =>
      expect(request).toHaveBeenCalledWith("painter@example.com"),
    );
  });

  it("shows the same confirmation regardless of whether the account exists", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "requestPasswordReset").mockResolvedValue({});
    renderWithProviders(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), "nobody@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(await screen.findByText(/if an account exists/i)).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/no account|not found|unknown/i);
  });

  it("surfaces a rate limit", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "requestPasswordReset").mockRejectedValue(
      new ApiError(429, "rate_limited", "Too many requests. Please wait a moment."),
    );
    renderWithProviders(<ForgotPasswordPage />);

    await user.type(screen.getByLabelText(/email/i), "painter@example.com");
    await user.click(screen.getByRole("button", { name: /send reset link/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/too many requests/i);
  });
});

describe("completing a reset", () => {
  const LINK = "/reset-password?uid=abc123&token=tok-456";

  it("rejects a link missing its parameters", () => {
    renderWithProviders(<ResetPasswordPage />, { route: "/reset-password" });
    expect(screen.getByText(/link is incomplete/i)).toBeInTheDocument();
  });

  it("requires the two passwords to match", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ResetPasswordPage />, { route: LINK });

    await user.type(screen.getByLabelText(/^new password/i), "a-long-enough-one");
    await user.type(screen.getByLabelText(/confirm/i), "a-different-one");

    expect(await screen.findByText(/do not match/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /set new password/i })).toBeDisabled();
  });

  it("enforces a minimum length", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ResetPasswordPage />, { route: LINK });

    await user.type(screen.getByLabelText(/^new password/i), "short");

    expect(await screen.findByText(/at least 8 characters/i)).toBeInTheDocument();
  });

  it("sends the uid and token from the link", async () => {
    const user = userEvent.setup();
    const confirm = vi
      .spyOn(api, "confirmPasswordReset")
      .mockResolvedValue({ access: "token-abc", user: makeUser() });
    renderWithProviders(<ResetPasswordPage />, { route: LINK });

    await user.type(screen.getByLabelText(/^new password/i), "a-brand-new-passphrase");
    await user.type(screen.getByLabelText(/confirm/i), "a-brand-new-passphrase");
    await user.click(screen.getByRole("button", { name: /set new password/i }));

    await waitFor(() =>
      expect(confirm).toHaveBeenCalledWith({
        uid: "abc123",
        token: "tok-456",
        new_password: "a-brand-new-passphrase",
      }),
    );
  });

  it("adopts the returned session rather than asking the user to sign in", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "confirmPasswordReset").mockResolvedValue({
      access: "token-abc",
      user: makeUser(),
    });
    renderWithProviders(<ResetPasswordPage />, { route: LINK });

    await user.type(screen.getByLabelText(/^new password/i), "a-brand-new-passphrase");
    await user.type(screen.getByLabelText(/confirm/i), "a-brand-new-passphrase");
    await user.click(screen.getByRole("button", { name: /set new password/i }));

    await waitFor(() => expect(getAccessToken()).toBe("token-abc"));
  });

  it("offers a fresh link when the token is rejected", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "confirmPasswordReset").mockRejectedValue(
      new ApiError(400, "invalid", "This reset link is invalid or has expired."),
    );
    renderWithProviders(<ResetPasswordPage />, { route: LINK });

    await user.type(screen.getByLabelText(/^new password/i), "a-brand-new-passphrase");
    await user.type(screen.getByLabelText(/confirm/i), "a-brand-new-passphrase");
    await user.click(screen.getByRole("button", { name: /set new password/i }));

    expect(await screen.findByText(/no longer valid/i)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /request a new link/i }),
    ).toBeInTheDocument();
  });

  it("shows a server-side password rejection against the field", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "confirmPasswordReset").mockRejectedValue(
      new ApiError(400, "invalid", "This password is too common.", {
        new_password: ["This password is too common."],
      }),
    );
    renderWithProviders(<ResetPasswordPage />, { route: LINK });

    await user.type(screen.getByLabelText(/^new password/i), "password123");
    await user.type(screen.getByLabelText(/confirm/i), "password123");
    await user.click(screen.getByRole("button", { name: /set new password/i }));

    expect(await screen.findByText(/too common/i)).toBeInTheDocument();

    expect(screen.queryByText(/no longer valid/i)).not.toBeInTheDocument();
  });
});

describe("email verification", () => {
  const LINK = "/verify-email?uid=abc123&token=tok-456";

  it("verifies automatically on arrival", async () => {
    const verify = vi
      .spyOn(api, "verifyEmail")
      .mockResolvedValue({ user: makeUser({ email_verified: true }) });
    renderWithProviders(<VerifyEmailPage />, { route: LINK });

    await waitFor(() =>
      expect(verify).toHaveBeenCalledWith({ uid: "abc123", token: "tok-456" }),
    );
    expect(await screen.findByText(/email confirmed/i)).toBeInTheDocument();
  });

  it("redeems the token only once", async () => {
    const verify = vi
      .spyOn(api, "verifyEmail")
      .mockResolvedValue({ user: makeUser({ email_verified: true }) });
    renderWithProviders(<VerifyEmailPage />, { route: LINK });

    await screen.findByText(/email confirmed/i);

    expect(verify).toHaveBeenCalledTimes(1);
  });

  it("explains an expired link", async () => {
    vi.spyOn(api, "verifyEmail").mockRejectedValue(
      new ApiError(400, "invalid", "This confirmation link is invalid or has expired."),
    );
    renderWithProviders(<VerifyEmailPage />, { route: LINK });

    expect(await screen.findByText(/could not confirm/i)).toBeInTheDocument();
  });

  it("rejects a link with no parameters without calling the API", async () => {
    const verify = vi.spyOn(api, "verifyEmail").mockResolvedValue({});
    renderWithProviders(<VerifyEmailPage />, { route: "/verify-email" });

    expect(await screen.findByText(/link is incomplete/i)).toBeInTheDocument();
    expect(verify).not.toHaveBeenCalled();
  });
});
