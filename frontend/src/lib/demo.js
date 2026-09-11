export function getDemoAccount() {
  const email = import.meta.env.VITE_DEMO_EMAIL?.trim() ?? "";
  const password = import.meta.env.VITE_DEMO_PASSWORD?.trim() ?? "";
  return email && password ? { email, password } : null;
}
