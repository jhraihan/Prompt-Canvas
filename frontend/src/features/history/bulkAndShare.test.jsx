import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { api } from "../../lib/api";
import { makeImage, renderWithProviders } from "../../test/utils";
import { HistoryPage } from "./HistoryPage";
import { SharedImagePage } from "../SharedImagePage";

const navigate = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigate,
    useParams: () => ({ token: "share-token-123" }),
  };
});

function page(results, next = null) {
  return { count: results.length, next, previous: null, results };
}

beforeEach(() => {
  navigate.mockReset();
  vi.spyOn(api, "restoreSession").mockResolvedValue(null);
});

describe("bulk selection", () => {
  const IMAGES = [
    makeImage({ id: 1, prompt: "First image" }),
    makeImage({ id: 2, prompt: "Second image" }),
    makeImage({ id: 3, prompt: "Third image" }),
  ];

  it("is off until asked for", async () => {
    vi.spyOn(api, "history").mockResolvedValue(page(IMAGES));
    renderWithProviders(<HistoryPage />);

    await screen.findByText("First image");
    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });

  it("shows a checkbox per card once enabled", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page(IMAGES));
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /^select$/i }));

    expect(screen.getAllByRole("checkbox")).toHaveLength(3);
  });

  it("keeps the delete action disabled until something is selected", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page(IMAGES));
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /^select$/i }));

    expect(screen.getByRole("button", { name: /delete selected/i })).toBeDisabled();
  });

  it("counts the selection", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page(IMAGES));
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /^select$/i }));
    await user.click(screen.getAllByRole("checkbox")[0]);
    await user.click(screen.getAllByRole("checkbox")[1]);

    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("selects every image at once", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page(IMAGES));
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /^select$/i }));
    await user.click(screen.getByRole("button", { name: /select all/i }));

    for (const box of screen.getAllByRole("checkbox")) {
      expect(box).toHaveAttribute("aria-checked", "true");
    }
  });

  it("confirms before deleting", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page(IMAGES));
    const removeMany = vi.spyOn(api, "removeMany").mockResolvedValue({ deleted: 2 });
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /^select$/i }));
    await user.click(screen.getAllByRole("checkbox")[0]);
    await user.click(screen.getByRole("button", { name: /delete selected/i }));

    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    expect(removeMany).not.toHaveBeenCalled();
  });

  it("sends only the selected ids", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page(IMAGES));
    const removeMany = vi.spyOn(api, "removeMany").mockResolvedValue({ deleted: 2 });
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /^select$/i }));
    await user.click(screen.getAllByRole("checkbox")[0]);
    await user.click(screen.getAllByRole("checkbox")[2]);
    await user.click(screen.getByRole("button", { name: /delete selected/i }));

    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: /delete 2/i }));

    await waitFor(() => expect(removeMany).toHaveBeenCalledWith([1, 3]));
  });

  it("removes the deleted cards", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page(IMAGES));
    vi.spyOn(api, "removeMany").mockResolvedValue({ deleted: 1 });
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /^select$/i }));
    await user.click(screen.getAllByRole("checkbox")[0]);
    await user.click(screen.getByRole("button", { name: /delete selected/i }));

    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: /delete 1/i }));

    await waitFor(() =>
      expect(screen.queryByText("First image")).not.toBeInTheDocument(),
    );
    expect(screen.getByText("Second image")).toBeInTheDocument();
  });

  it("leaves selection mode when cancelled", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page(IMAGES));
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /^select$/i }));
    await user.click(screen.getByRole("button", { name: /^done$/i }));

    expect(screen.queryByRole("checkbox")).not.toBeInTheDocument();
  });
});

describe("share links", () => {
  it("opens the share dialog from a card", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page([makeImage()]));
    vi.spyOn(api, "shareLinks").mockResolvedValue([]);
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /share this image/i }));

    expect(await screen.findByRole("dialog", { name: /share this image/i })).toBeInTheDocument();
  });

  it("warns that the file URL cannot be revoked", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page([makeImage()]));
    vi.spyOn(api, "shareLinks").mockResolvedValue([]);
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /share this image/i }));

    expect(await screen.findByText(/cannot be/i)).toBeInTheDocument();
  });

  it("creates a link with the chosen lifetime", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page([makeImage()]));
    vi.spyOn(api, "shareLinks").mockResolvedValue([]);
    const create = vi.spyOn(api, "createShareLink").mockResolvedValue({
      id: 7,
      token: "tok",
      url: "http://localhost:5173/shared/tok",
      active: true,
      expires_at: "2026-09-17T00:00:00Z",
      view_count: 0,
    });
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /share this image/i }));
    await screen.findByRole("dialog");
    await user.click(screen.getByRole("radio", { name: /1 day/i }));
    await user.click(screen.getByRole("button", { name: /create share link/i }));

    await waitFor(() => expect(create).toHaveBeenCalledWith(42, 24));
  });

  it("lists an active link and can revoke it", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "history").mockResolvedValue(page([makeImage()]));
    vi.spyOn(api, "shareLinks").mockResolvedValue([
      {
        id: 7,
        token: "tok",
        url: "http://localhost:5173/shared/tok",
        active: true,
        expires_at: "2026-09-17T00:00:00Z",
        view_count: 3,
      },
    ]);
    const revoke = vi.spyOn(api, "revokeShareLink").mockResolvedValue(undefined);
    renderWithProviders(<HistoryPage />);

    await user.click(await screen.findByRole("button", { name: /share this image/i }));
    expect(await screen.findByText(/shared\/tok/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /revoke this link/i }));

    await waitFor(() => expect(revoke).toHaveBeenCalledWith(7));
  });
});

describe("the public shared page", () => {
  it("renders a shared image without a session", async () => {
    vi.spyOn(api, "sharedImage").mockResolvedValue({
      prompt: "A shared harbour",
      image_url: "http://localhost:8000/media/generated/1/abc.png",
      size: "1024x1024",
      width: 1024,
      height: 1024,
      created_at: "2026-08-25T09:30:00Z",
    });
    renderWithProviders(<SharedImagePage />, { route: "/shared/share-token-123" });

    expect(await screen.findByText("A shared harbour")).toBeInTheDocument();
    expect(screen.getByAltText(/generated image: a shared harbour/i)).toBeInTheDocument();
  });

  it("explains a dead link without saying why", async () => {
    vi.spyOn(api, "sharedImage").mockRejectedValue(new Error("404"));
    renderWithProviders(<SharedImagePage />, { route: "/shared/share-token-123" });

    expect(await screen.findByText(/not available/i)).toBeInTheDocument();

    expect(document.body.textContent).not.toMatch(/revoked|expired on/i);
  });
});
