import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, api, getAccessToken, setAccessToken, setSessionEndedHandler } from "./api";

function jsonResponse(status, body) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function fetchMock() {
  const mock = vi.fn();
  vi.stubGlobal("fetch", mock);
  return mock;
}

beforeEach(() => {
  setAccessToken(null);
  setSessionEndedHandler(null);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("credentials", () => {
  it("sends cookies on every request so the refresh cookie travels", async () => {
    const fetch = fetchMock();
    fetch.mockResolvedValue(jsonResponse(200, { sizes: [], qualities: [] }));

    await api.options();

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/images/options/"),
      expect.objectContaining({ credentials: "include" }),
    );
  });

  it("attaches the access token as a bearer header", async () => {
    const fetch = fetchMock();
    fetch.mockResolvedValue(jsonResponse(200, { results: [] }));
    setAccessToken("token-123");

    await api.history();

    const [, init] = fetch.mock.calls[0];
    expect(init.headers.Authorization).toBe("Bearer token-123");
  });

  it("omits the header when there is no token", async () => {
    const fetch = fetchMock();
    fetch.mockResolvedValue(jsonResponse(200, {}));

    await api.options();

    const [, init] = fetch.mock.calls[0];
    expect(init.headers.Authorization).toBeUndefined();
  });

  it("keeps the access token out of persistent storage", async () => {
    const fetch = fetchMock();
    fetch.mockResolvedValue(
      jsonResponse(200, { access: "token-abc", user: { id: 1, email: "a@b.c" } }),
    );

    await api.login({ email: "a@b.c", password: "secret" });

    expect(window.localStorage.getItem("access")).toBeNull();
    expect(JSON.stringify(window.localStorage)).not.toContain("token-abc");
    expect(JSON.stringify(window.sessionStorage)).not.toContain("token-abc");
  });
});

describe("automatic refresh", () => {
  it("refreshes once on a 401 and replays the request", async () => {
    const fetch = fetchMock();
    setAccessToken("stale");

    fetch
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Token expired", code: "unauthenticated" }))
      .mockResolvedValueOnce(jsonResponse(200, { access: "fresh", user: { id: 1 } }))
      .mockResolvedValueOnce(jsonResponse(200, { count: 0, results: [] }));

    const result = await api.history();

    expect(result.count).toBe(0);
    expect(fetch).toHaveBeenCalledTimes(3);
    expect(fetch.mock.calls[1][0]).toContain("/api/auth/refresh/");
    expect(getAccessToken()).toBe("fresh");

    expect(fetch.mock.calls[2][1].headers.Authorization).toBe("Bearer fresh");
  });

  it("ends the session when the refresh also fails", async () => {
    const fetch = fetchMock();
    const onEnded = vi.fn();
    setSessionEndedHandler(onEnded);
    setAccessToken("stale");

    fetch
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Token expired" }))
      .mockResolvedValueOnce(jsonResponse(401, { detail: "Your session has ended." }));

    await expect(api.history()).rejects.toBeInstanceOf(ApiError);
    expect(onEnded).toHaveBeenCalledOnce();
    expect(getAccessToken()).toBeNull();
  });

  it("does not attempt to refresh a failed login", async () => {
    const fetch = fetchMock();
    fetch.mockResolvedValue(jsonResponse(401, { detail: "No active account found" }));

    await expect(api.login({ email: "a@b.c", password: "wrong" })).rejects.toBeInstanceOf(
      ApiError,
    );
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it("collapses parallel 401s into a single refresh", async () => {
    const fetch = fetchMock();
    setAccessToken("stale");

    fetch.mockImplementation((url) => {
      if (url.includes("/api/auth/refresh/")) {
        return Promise.resolve(jsonResponse(200, { access: "fresh", user: { id: 1 } }));
      }
      return Promise.resolve(
        fetch.mock.calls.filter((call) => !String(call[0]).includes("refresh"))
          .length <= 2
          ? jsonResponse(401, { detail: "Token expired" })
          : jsonResponse(200, { count: 0, results: [] }),
      );
    });

    await Promise.all([api.history(), api.history()]);

    const refreshCalls = fetch.mock.calls.filter((call) =>
      String(call[0]).includes("/api/auth/refresh/"),
    );
    expect(refreshCalls).toHaveLength(1);
  });
});

describe("error translation", () => {
  it("surfaces the server detail and code", async () => {
    const fetch = fetchMock();
    fetch.mockResolvedValue(
      jsonResponse(429, { detail: "Too many images right now.", code: "rate_limited" }),
    );

    await expect(api.generate({ prompt: "x", size: "1024x1024", quality: "standard" }))
      .rejects.toMatchObject({ status: 429, code: "rate_limited", message: "Too many images right now." });
  });

  it("collects field errors from a validation response", async () => {
    const fetch = fetchMock();
    fetch.mockResolvedValue(
      jsonResponse(400, { prompt: ["Describe the image you want to generate."] }),
    );

    try {
      await api.generate({ prompt: "", size: "1024x1024", quality: "standard" });
      expect.unreachable("should have thrown");
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error).fieldError("prompt")).toBe(
        "Describe the image you want to generate.",
      );
    }
  });

  it("reports a network failure as a readable message", async () => {
    const fetch = fetchMock();
    fetch.mockRejectedValue(new TypeError("Failed to fetch"));

    try {
      await api.options();
      expect.unreachable("should have thrown");
    } catch (error) {
      expect((error).isNetworkError).toBe(true);
      expect((error).message).toMatch(/could not reach prompt canvas/i);
    }
  });

  it("falls back to a plain message when the body is not JSON", async () => {
    const fetch = fetchMock();
    fetch.mockResolvedValue(new Response("<html>502</html>", { status: 502 }));

    await expect(api.options()).rejects.toMatchObject({
      status: 502,
      message: "Something went wrong on our side. Please try again.",
    });
  });

  it("handles a 204 with no body", async () => {
    const fetch = fetchMock();
    fetch.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(api.remove(1)).resolves.toBeUndefined();
  });
});

describe("logout", () => {
  it("clears the in-memory token even if the request fails", async () => {
    const fetch = fetchMock();
    setAccessToken("token-123");
    fetch.mockRejectedValue(new TypeError("Failed to fetch"));

    await expect(api.logout()).rejects.toBeInstanceOf(ApiError);
    expect(getAccessToken()).toBeNull();
  });
});
