import { allowDevAuth } from "./clientConfig";
import { getTelegramInitData } from "./telegram";

export function buildAuthHeaders(jsonBody = false, visitId = null) {
  const headers = {};
  if (jsonBody) {
    headers["Content-Type"] = "application/json";
  }

  const initData = getTelegramInitData();
  if (initData) {
    headers["X-Telegram-Init-Data"] = initData;
  } else if (allowDevAuth()) {
    headers["X-Dev-Mode"] = "1";
  }

  if (visitId) {
    headers["X-Visit-Id"] = visitId;
  }

  return headers;
}

async function parseJsonSafe(response) {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
}

export async function apiRequest(path, options = {}) {
  const { method = "GET", body, json = body !== undefined, visitId = null } = options;
  const headers = {
    ...buildAuthHeaders(json, visitId),
    ...(options.headers || {}),
  };

  const response = await fetch(path, {
    method,
    headers,
    body: json && body !== undefined ? JSON.stringify(body) : body,
    credentials: "same-origin",
  });

  const data = await parseJsonSafe(response);

  if (!response.ok) {
    const message =
      (data && (data.detail || data.message)) ||
      `Request failed (${response.status})`;
    const error = new Error(typeof message === "string" ? message : JSON.stringify(message));
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

export const api = {
  getMe() {
    return apiRequest("/api/me");
  },

  postSessionStart(payload) {
    return apiRequest("/api/session/start", { method: "POST", body: payload });
  },

  postSessionStop(payload) {
    return apiRequest("/api/session/stop", { method: "POST", body: payload });
  },

  postTasbehSync(payload, visitId) {
    return apiRequest("/api/tasbeh/sync", { method: "POST", body: payload, visitId });
  },

  postVisitHeartbeat(body, visitId) {
    return apiRequest("/api/visit/heartbeat", { method: "POST", body, visitId });
  },

  postVisitSnapshot() {
    return apiRequest("/api/visit/snapshot", { method: "POST" });
  },

  getProgress() {
    return apiRequest("/api/progress");
  },

  adminOverview() {
    return apiRequest("/api/admin/overview");
  },

  adminUsers(params) {
    const q = new URLSearchParams(params).toString();
    return apiRequest(`/api/admin/users?${q}`);
  },

  adminUser(id) {
    return apiRequest(`/api/admin/users/${id}`);
  },

  adminDaily(days = 30) {
    return apiRequest(`/api/admin/daily?days=${days}`);
  },

  adminFunnel(days = 7) {
    return apiRequest(`/api/admin/funnel?days=${days}`);
  },
};
