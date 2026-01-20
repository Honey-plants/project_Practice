// src/common/utils/authApi.js

import { apiFetch, authFetch } from "./httpClient";
import { setSession, clearSession } from "./session";

const LOGIN_URL = "/auth/login";
const ME_URL = "/auth/me";
const LOGOUT_URL = "/auth/logout";

export async function login({ email, password }) {
  // FastAPI OAuth2PasswordRequestForm: application/x-www-form-urlencoded
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const tokenData = await apiFetch(LOGIN_URL, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
    credentials: "include", // refresh cookie 세팅 받기
  });

  const accessToken = tokenData?.access_token;
  if (!accessToken) throw new Error("No access token in login response.");

  const me = await fetchMe(accessToken);

  const sessionObj = {
    access_token: accessToken,
    member_id: me?.member_id,
    nickname: me?.nickname ?? "",
  };
  setSession(sessionObj);
  return { session: sessionObj, me };
}

export async function fetchMe(accessToken) {
  const res = await fetch(ME_URL, {
    method: "GET",
    headers: { Authorization: `Bearer ${accessToken}` },
    credentials: "include",
  });

  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }

  if (!res.ok) {
    const msg = (data && typeof data === "object" && data.detail) || `HTTP ${res.status}`;
    throw new Error(msg);
  }
  return data;
}

export async function logout() {
  try {
    await authFetch(LOGOUT_URL, { method: "POST" });
  } finally {
    clearSession();
  }
}
