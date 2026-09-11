import { BrowserRouter, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/layout/AppShell";
import { ToastProvider } from "./components/ui/Toast";
import { LoginPage } from "./features/auth/LoginPage";
import { ProtectedRoute } from "./features/auth/ProtectedRoute";
import { RegisterPage } from "./features/auth/RegisterPage";
import { ForgotPasswordPage } from "./features/auth/ForgotPasswordPage";
import { ResetPasswordPage } from "./features/auth/ResetPasswordPage";
import { VerifyEmailPage } from "./features/auth/VerifyEmailPage";
import { SharedImagePage } from "./features/SharedImagePage";
import { LandingPage } from "./features/marketing/LandingPage";
import { GeneratorPage } from "./features/generator/GeneratorPage";
import { HistoryPage } from "./features/history/HistoryPage";
import { NotFoundPage } from "./features/NotFoundPage";
import { Spinner } from "./components/ui/Spinner";
import { AuthProvider, useAuth } from "./lib/auth";
import { ThemeProvider } from "./lib/theme";

function ShellRoute({ children }) {
  return (
    <ProtectedRoute>
      <AppShell>{children}</AppShell>
    </ProtectedRoute>
  );
}

function HomeRoute() {
  const { status } = useAuth();

  if (status === "loading") {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-canvas">
        <Spinner size={22} label="Loading" />
      </div>
    );
  }

  if (status === "anonymous") return <LandingPage />;

  return (
    <AppShell>
      <GeneratorPage />
    </AppShell>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
                            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="/verify-email" element={<VerifyEmailPage />} />
                            <Route path="/shared/:token" element={<SharedImagePage />} />
              <Route path="/" element={<HomeRoute />} />
              <Route
                path="/history"
                element={
                  <ShellRoute>
                    <HistoryPage />
                  </ShellRoute>
                }
              />
              <Route
                path="*"
                element={
                  <ShellRoute>
                    <NotFoundPage />
                  </ShellRoute>
                }
              />
            </Routes>
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}
