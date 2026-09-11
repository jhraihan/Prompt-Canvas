const BASE = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(
  /\/$/,
  "",
);

export class ApiError extends Error {

  constructor(status, code, message, fieldErrors = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors;
  }

  fieldError(name) {
    return this.fieldErrors[name]?.[0];
  }

  get isNetworkError() {
    return this.status === 0;
  }
}

let accessToken = null;
let onSessionEnded = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

export function setSessionEndedHandler(handler) {
  onSessionEnded = handler;
}

function parseErrorBody(status, body) {
  if (body && typeof body === "object") {
    const code = typeof body.code === "string" ? body.code : "error";
    const detail = typeof body.detail === "string" ? body.detail : null;

    const fieldErrors = {};
    for (const [key, value] of Object.entries(body)) {
      if (key === "detail" || key === "code") continue;
      if (Array.isArray(value)) {
        fieldErrors[key] = value.map(String);
      } else if (typeof value === "string") {
        fieldErrors[key] = [value];
      }
    }

    const firstField = Object.values(fieldErrors)[0]?.[0];
    return new ApiError(status, code, detail ?? firstField ?? fallbackMessage(status), fieldErrors);
  }
  return new ApiError(status, "error", fallbackMessage(status));
}

function fallbackMessage(status) {
  if (status === 401) return "Please sign in to continue.";
  if (status === 403) return "You do not have access to that.";
  if (status === 404) return "That item no longer exists.";
  if (status === 429) return "Too many requests. Please wait a moment and try again.";
  if (status >= 500) return "Something went wrong on our side. Please try again.";
  return "Something went wrong. Please try again.";
}

let refreshInFlight = null;

async function rawRequest(path, options) {
  const { method = "GET", body, signal } = options;

  const headers = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;

  let response;
  try {
    response = await fetch(`${BASE}${path}`, {
      method,
      headers,

      credentials: "include",
      body: body === undefined ? undefined : JSON.stringify(body),
      signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    throw new ApiError(
      0,
      "network_error",
      "Could not reach Prompt Canvas. Check your connection and try again.",
    );
  }

  if (response.status === 204) return undefined;

  const text = await response.text();
  const payload = text ? safeJson(text) : null;

  if (!response.ok) throw parseErrorBody(response.status, payload);
  return payload;
}

function safeJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

async function request(path, options = {}) {
  try {
    return await rawRequest(path, options);
  } catch (error) {
    const isExpiredAccess =
      error instanceof ApiError && error.status === 401 && !options.skipRefresh;
    if (!isExpiredAccess) throw error;

    const renewed = await refreshOnce();
    if (!renewed) {
      onSessionEnded?.();
      throw error;
    }
    return rawRequest(path, { ...options, skipRefresh: true });
  }
}

async function refreshOnce() {
  refreshInFlight ??= (async () => {
    try {
      const result = await rawRequest("/api/auth/refresh/", {
        method: "POST",
        skipRefresh: true,
      });
      accessToken = result.access;
      return result;
    } catch {
      accessToken = null;
      return null;
    } finally {

      queueMicrotask(() => {
        refreshInFlight = null;
      });
    }
  })();
  return refreshInFlight;
}

export const api = {
  register(input) {
    return request("/api/auth/register/", { method: "POST", body: input });
  },

  login(input) {
    return request("/api/auth/login/", {
      method: "POST",
      body: input,
      skipRefresh: true,
    });
  },

  restoreSession() {
    return refreshOnce();
  },

  async logout() {
    try {
      await request("/api/auth/logout/", { method: "POST", skipRefresh: true });
    } finally {
      accessToken = null;
    }
  },

  me() {
    return request("/api/auth/me/");
  },

  updateProfile(input) {
    return request("/api/auth/me/", { method: "PATCH", body: input });
  },

  requestPasswordReset(email) {
    return request("/api/auth/password/reset/", {
      method: "POST",
      body: { email },
      skipRefresh: true,
    });
  },

  confirmPasswordReset(input) {
    return request("/api/auth/password/reset/confirm/", {
      method: "POST",
      body: input,
      skipRefresh: true,
    });
  },

  verifyEmail(input) {
    return request("/api/auth/email/verify/", {
      method: "POST",
      body: input,
      skipRefresh: true,
    });
  },

  resendVerification() {
    return request("/api/auth/email/verify/request/", { method: "POST" });
  },

  changePassword(input) {
    return request("/api/auth/password/", { method: "POST", body: input });
  },

  options() {
    return request("/api/images/options/");
  },

  generate(input, signal) {
    return request("/api/images/generate/", {
      method: "POST",
      body: input,
      signal,
    });
  },

  history(page = 1, pageSize = 12) {
    return request(`/api/images/?page=${page}&page_size=${pageSize}`);
  },

  image(id) {
    return request(`/api/images/${id}/`);
  },

  remove(id) {
    return request(`/api/images/${id}/`, { method: "DELETE" });
  },

  removeMany(ids) {
    return request("/api/images/bulk-delete/", {
      method: "POST",
      body: { ids },
    });
  },

  quota() {
    return request("/api/images/quota/");
  },

  savedPrompts() {
    return request("/api/images/prompts/");
  },

  savePrompt(input) {
    return request("/api/images/prompts/", { method: "POST", body: input });
  },

  updateSavedPrompt(id, input) {
    return request(`/api/images/prompts/${id}/`, { method: "PATCH", body: input });
  },

  deleteSavedPrompt(id) {
    return request(`/api/images/prompts/${id}/`, { method: "DELETE" });
  },

  useSavedPrompt(id) {
    return request(`/api/images/prompts/${id}/use/`, { method: "POST" });
  },

  shareLinks(imageId) {
    return request(`/api/images/${imageId}/share/`);
  },

  createShareLink(imageId, expiresInHours) {
    return request(`/api/images/${imageId}/share/`, {
      method: "POST",
      body: expiresInHours ? { expires_in_hours: expiresInHours } : {},
    });
  },

  revokeShareLink(shareId) {
    return request(`/api/images/shares/${shareId}/`, { method: "DELETE" });
  },

  sharedImage(token) {
    return request(`/api/images/shared/${token}/`, { skipRefresh: true });
  },
};

export { BASE as API_BASE_URL };
