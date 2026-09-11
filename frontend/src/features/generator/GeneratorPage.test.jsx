import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api } from "../../lib/api";
import { makeImage, renderWithProviders } from "../../test/utils";
import { GeneratorPage } from "./GeneratorPage";

const OPTIONS = {
  sizes: [
    { value: "1024x1024", label: "Square", aspect: "1024 / 1024" },
    { value: "1024x1536", label: "Portrait", aspect: "1024 / 1536" },
    { value: "1536x1024", label: "Landscape", aspect: "1536 / 1024" },
  ],
  qualities: [
    { value: "standard", label: "Standard" },
    { value: "hd", label: "High detail" },
  ],
  provider: "huggingface",
  model: "black-forest-labs/FLUX.1-schnell",
};

beforeEach(() => {
  vi.spyOn(api, "restoreSession").mockResolvedValue(null);
  vi.spyOn(api, "options").mockResolvedValue(OPTIONS);
});

function generateButton() {
  return screen.getByRole("button", { name: /generate image/i });
}

describe("prompt validation", () => {
  it("disables Generate while the prompt is empty", async () => {
    renderWithProviders(<GeneratorPage />);
    expect(generateButton()).toBeDisabled();
  });

  it("enables Generate once the prompt is long enough", async () => {
    const user = userEvent.setup();
    renderWithProviders(<GeneratorPage />);
    await user.type(screen.getByLabelText(/describe your image/i), "a fox");
    expect(generateButton()).toBeEnabled();
  });

  it("shows an error when the prompt is too short", async () => {
    const user = userEvent.setup();
    renderWithProviders(<GeneratorPage />);
    const field = screen.getByLabelText(/describe your image/i);
    await user.type(field, "ab");
    await user.tab();
    expect(await screen.findByRole("alert")).toHaveTextContent(/at least 3 characters/i);
  });

  it("shows an error when a blurred prompt is empty", async () => {
    const user = userEvent.setup();
    renderWithProviders(<GeneratorPage />);
    await user.click(screen.getByLabelText(/describe your image/i));
    await user.tab();
    expect(await screen.findByRole("alert")).toHaveTextContent(/describe the image/i);
  });

  it("counts characters against the limit", async () => {
    const user = userEvent.setup();
    renderWithProviders(<GeneratorPage />);
    await user.type(screen.getByLabelText(/describe your image/i), "a fox");
    expect(screen.getByText("5 / 1000")).toBeInTheDocument();
  });
});

describe("submission", () => {
  it("sends the prompt, size, and quality", async () => {
    const user = userEvent.setup();
    const generate = vi.spyOn(api, "generate").mockResolvedValue(makeImage());
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "a snow leopard");
    await user.click(screen.getByRole("radio", { name: /portrait/i }));
    await user.click(screen.getByRole("radio", { name: /high detail/i }));
    await user.click(generateButton());

    await waitFor(() =>
      expect(generate).toHaveBeenCalledWith(
        { prompt: "a snow leopard", size: "1024x1536", quality: "hd" },
        expect.anything(),
      ),
    );
  });

  it("trims the prompt before sending", async () => {
    const user = userEvent.setup();
    const generate = vi.spyOn(api, "generate").mockResolvedValue(makeImage());
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "  a windmill  ");
    await user.click(generateButton());

    await waitFor(() =>
      expect(generate).toHaveBeenCalledWith(
        expect.objectContaining({ prompt: "a windmill" }),
        expect.anything(),
      ),
    );
  });

  it("does not start a second generation while one is in flight", async () => {
    const user = userEvent.setup();
    const generate = vi
      .spyOn(api, "generate")
      .mockImplementation(() => new Promise(() => {}));
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "a harbour");

    const button = generateButton();
    await user.click(button);
    await user.click(button);

    expect(generate).toHaveBeenCalledTimes(1);
    expect(button).toBeDisabled();
  });
});

describe("loading state", () => {
  it("announces that generation is under way and disables the button", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "generate").mockImplementation(() => new Promise(() => {}));
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "a harbour");
    await user.click(generateButton());

    expect(await screen.findByText(/generating image/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /generating/i })).toBeDisabled();
  });

  it("preserves the prompt and settings during generation", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "generate").mockImplementation(() => new Promise(() => {}));
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "a harbour at dusk");
    await user.click(screen.getByRole("radio", { name: /landscape/i }));
    await user.click(generateButton());

    expect(screen.getByLabelText(/describe your image/i)).toHaveValue("a harbour at dusk");
    expect(screen.getByRole("radio", { name: /landscape/i })).toBeChecked();
  });
});

describe("successful generation", () => {
  it("renders the image with the prompt as alt text", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "generate").mockResolvedValue(
      makeImage({ prompt: "A futuristic city at sunset" }),
    );
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "A futuristic city at sunset");
    await user.click(generateButton());

    const image = await screen.findByAltText(/generated image: a futuristic city at sunset/i);
    expect(image).toHaveAttribute("src", expect.stringContaining("abc.png"));
  });

  it("shows the metadata the PRD requires", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "generate").mockResolvedValue(makeImage({ size: "1536x1024", quality: "hd" }));
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "a wide valley");
    await user.click(generateButton());

    await screen.findByAltText(/generated image/i);
    const result = screen.getByRole("region", { name: /result/i });
    expect(within(result).getByText("1536 x 1024")).toBeInTheDocument();
    expect(within(result).getByText("High detail")).toBeInTheDocument();
    expect(within(result).getByText("FLUX.1-schnell")).toBeInTheDocument();
  });

  it("offers download and regenerate", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "generate").mockResolvedValue(makeImage());
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "a lighthouse");
    await user.click(generateButton());

    await screen.findByAltText(/generated image/i);
    const result = screen.getByRole("region", { name: /result/i });
    expect(within(result).getByRole("button", { name: /^download$/i })).toBeInTheDocument();
    expect(within(result).getByRole("button", { name: /regenerate/i })).toBeInTheDocument();
  });

  it("replaces the empty state", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "generate").mockResolvedValue(makeImage());
    renderWithProviders(<GeneratorPage />);

    expect(screen.getByText(/your generated image will appear here/i)).toBeInTheDocument();

    await user.type(screen.getByLabelText(/describe your image/i), "a lighthouse");
    await user.click(generateButton());

    await screen.findByAltText(/generated image/i);
    expect(screen.queryByText(/your generated image will appear here/i)).not.toBeInTheDocument();
  });
});

describe("empty state", () => {
  it("explains what to do before the first generation", () => {
    renderWithProviders(<GeneratorPage />);
    expect(screen.getByText(/your generated image will appear here/i)).toBeInTheDocument();
    expect(screen.getByText(/describe an image on the left/i)).toBeInTheDocument();
  });
});

describe("error state", () => {
  it("shows a safe message and keeps the prompt", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "generate").mockRejectedValue(
      new ApiError(504, "timeout", "The image took too long to generate. Please try again."),
    );
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "a stormy sea");
    await user.click(generateButton());

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText(/took too long/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/describe your image/i)).toHaveValue("a stormy sea");
  });

  it("offers a retry that generates again", async () => {
    const user = userEvent.setup();
    const generate = vi
      .spyOn(api, "generate")
      .mockRejectedValueOnce(new ApiError(502, "generation_failed", "Could not generate."))
      .mockResolvedValueOnce(makeImage());
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "a stormy sea");
    await user.click(generateButton());

    await user.click(await screen.findByRole("button", { name: /try again/i }));
    await screen.findByAltText(/generated image/i);
    expect(generate).toHaveBeenCalledTimes(2);
  });

  it("shows rate limiting next to the generate control", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "generate").mockRejectedValue(
      new ApiError(429, "rate_limited", "Too many images are being generated right now."),
    );
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "a stormy sea");
    await user.click(generateButton());

    expect(await screen.findByText(/slow down a moment/i)).toBeInTheDocument();
  });

  it("never renders a raw provider error", async () => {
    const user = userEvent.setup();
    vi.spyOn(api, "generate").mockRejectedValue(
      new ApiError(503, "provider_unconfigured", "Image generation is not configured correctly."),
    );
    renderWithProviders(<GeneratorPage />);

    await user.type(screen.getByLabelText(/describe your image/i), "a stormy sea");
    await user.click(generateButton());

    await screen.findByRole("alert");
    expect(document.body.textContent).not.toMatch(/hf_/i);
    expect(document.body.textContent).not.toMatch(/traceback/i);
  });
});

describe("prompt guide", () => {
  it("is collapsed until asked for", async () => {
    const user = userEvent.setup();
    renderWithProviders(<GeneratorPage />);

    const toggle = screen.getByRole("button", { name: /how to write a good prompt/i });
    expect(toggle).toHaveAttribute("aria-expanded", "false");

    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText(/environment/i)).toBeInTheDocument();
  });

  it("can fill the prompt with the worked example", async () => {
    const user = userEvent.setup();
    renderWithProviders(<GeneratorPage />);

    await user.click(screen.getByRole("button", { name: /how to write a good prompt/i }));
    await user.click(screen.getByRole("button", { name: /use this example prompt/i }));

    const field = screen.getByLabelText(/describe your image/i);
    expect(field.value).toContain("snow leopard");
    expect(field.value).toContain("golden hour backlight");
  });
});

describe("regenerate handoff", () => {
  it("prefills the prompt and settings from router state", async () => {
    renderWithProviders(<GeneratorPage />, {
      routerState: { prompt: "a copper teapot", size: "1536x1024", quality: "hd" },
    });

    expect(screen.getByLabelText(/describe your image/i)).toHaveValue("a copper teapot");
    expect(screen.getByRole("radio", { name: /landscape/i })).toBeChecked();
    expect(screen.getByRole("radio", { name: /high detail/i })).toBeChecked();
  });
});
