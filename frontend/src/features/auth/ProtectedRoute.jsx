import { Navigate, useLocation } from "react-router-dom";

import { Spinner } from "../../components/ui/Spinner";
import { useAuth } from "../../lib/auth";

export function ProtectedRoute({ children }) {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-canvas">
        <Spinner size={22} label="Restoring your session" />
      </div>
    );
  }

  if (status === "anonymous") {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <>{children}</>;
}
