// src/common/utils/httpClient.js
// fetch 래퍼: JSON 처리 + Authorization 자동 부착

import { getAccessToken, clearSession } from "./session";

function buildHeaders(headers = {}, { json = false } = {}) {
  const h = new Headers(headers);
  if (json && !h.has("Content-Type")) h.set("Content-Type", "application/json");
  return h;
}

async function readBody(res) {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export async function apiFetch(url, options = {}) {
  const res = await fetch(url, options);
  const data = await readBody(res);

  if (!res.ok) {
    const msg =
      (data && typeof data === "object" && (data.detail || data.message)) ||
      `HTTP ${res.status}`;
    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}


export async function authFetch(url, options = {}) {
  const token = getAccessToken();
  const headers = buildHeaders(options.headers, options.json ? { json: true } : {});

  if (token) headers.set("Authorization", `Bearer ${token}`);

  console.log("[AUTH FETCH]", url, {
    hasToken: !!token,
    tokenPreview: token ? token.slice(0, 12) + "..." : null,
  });

  const res = await fetch(url, {
    ...options,
    headers,
    credentials: "include", // refresh 쿠키(백엔드가 지원하면) 대비
  });

  // 401이면 세션 무효화(현 백엔드는 refresh를 body로 받기 때문에 프론트에서 복구 불가)
  if (res.status === 401) {
    clearSession();
  }

  const data = await readBody(res);

  if (!res.ok) {
    const msg =
      (data && typeof data === "object" && (data.detail || data.message)) ||
      `HTTP ${res.status}`;
    const err = new Error(msg);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}
