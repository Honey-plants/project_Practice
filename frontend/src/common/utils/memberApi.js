// src/common/utils/memberApi.js

import { apiFetch, authFetch } from "./httpClient";

export function signupMember(payload) {
  return apiFetch("/members", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function getMember(member_id) {
  return authFetch(`/members/${member_id}`, { method: "GET" });
}

export function updateMember(member_id, payload) {
  return authFetch(`/members/${member_id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function checkNickname(nickname) {
  const qs = new URLSearchParams({ nickname });
  return apiFetch(`/members/nickname/check?${qs.toString()}`);
}
