// src/utils/jwt.js
// 프론트에서 "권한 분기" 정도만 하기 위한 간단 파서
// (서명 검증은 하지 않음: 서버가 검증 주체)

function base64UrlToJson(input) {
  try {
    const base64 = input.replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
    const decoded = atob(padded);

    // UTF-8 안전 처리
    const json = decodeURIComponent(
      decoded
        .split("")
        .map((c) => `%${c.charCodeAt(0).toString(16).padStart(2, "0")}`)
        .join("")
    );

    return JSON.parse(json);
  } catch {
    return null;
  }
}

export function parseJwt(token) {
  if (!token || typeof token !== "string") return null;
  const parts = token.split(".");
  if (parts.length < 2) return null;
  return base64UrlToJson(parts[1]);
}

export function getJwtRole(token) {
  const payload = parseJwt(token);
  return payload?.role || payload?.roles || null;
}
