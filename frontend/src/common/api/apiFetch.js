const ACCESS_KEY = "accessToken";
const BASE = process.env.REACT_APP_API_BASE_URL || "";

export function getAccessToken() {
  return sessionStorage.getItem(ACCESS_KEY);
}
export function setAccessToken(token) {
  if (token) sessionStorage.setItem(ACCESS_KEY, token);
  else sessionStorage.removeItem(ACCESS_KEY);
  window.dispatchEvent(new Event("auth-changed"));
}

export async function apiFetch(url, options = {}, retry = true) {
  // 회원가입의 경우 token이 없으므로 401 호출 하지만 필요가 없음
  const skipRefresh = options.skipRefresh === true; // 추가
  const token = getAccessToken();
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const res = await fetch(BASE + url, { ...options, headers, credentials: "include" });

  if (!skipRefresh && res.status === 401 && retry) {
    const refreshed = await fetch(BASE + "/auth/refresh", { method: "POST", credentials: "include" });
    if (!refreshed.ok) {
      setAccessToken(null);
      throw new Error("세션이 만료되었습니다. 다시 로그인 해주세요.");
    }
    const data = await refreshed.json();
    setAccessToken(data.access_token);
    return apiFetch(url, options, false);
  }
  return res;
}