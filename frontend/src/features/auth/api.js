import { apiFetch } from "common/api/apiFetch";

export async function logout() {
  const res = await apiFetch("/auth/logout", {
    method: "POST",
  });

  if (!res.ok) {
    // 서버가 detail 주면 그걸 우선
    let err = {};
    try { err = await res.json(); } catch (_) {}
    throw new Error(err?.detail || `로그아웃 실패 (${res.status})`);
  }
  return res.json(); // { ok: true }
}