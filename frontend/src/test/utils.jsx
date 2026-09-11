import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { ToastProvider } from "../components/ui/Toast";
import { AuthProvider } from "../lib/auth";
import { ThemeProvider } from "../lib/theme";

export function makeUser(overrides = {}) {
  return {
    id: 1,
    email: "painter@example.com",
    display_name: "Painter",
    date_joined: "2026-08-01T10:00:00Z",
    ...overrides,
  };
}

export function makeImage(overrides = {}) {
  return {
    id: 42,
    prompt: "A futuristic city at sunset",
    image_url: "http://localhost:8000/media/generated/1/abc.png",
    size: "1024x1024",
    quality: "standard",
    provider: "huggingface",
    model: "black-forest-labs/FLUX.1-schnell",
    width: 1024,
    height: 1024,
    byte_size: 512_000,
    download_filename: "promptcanvas-a-futuristic-city-at-sunset-20260825-093000.png",
    created_at: "2026-08-25T09:30:00Z",
    ...overrides,
  };
}

function Providers({ children }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>{children}</ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export function renderWithProviders(ui, options = {}) {
  const { route = "/", routerState, ...rest } = options;

  const [pathname, ...queryParts] = route.split("?");
  const search = queryParts.length > 0 ? `?${queryParts.join("?")}` : "";

  return render(ui, {
    wrapper: ({ children }) => (
      <MemoryRouter
        initialEntries={[{ pathname, search, state: routerState }]}
      >
        <Providers>{children}</Providers>
      </MemoryRouter>
    ),
    ...rest,
  });
}
