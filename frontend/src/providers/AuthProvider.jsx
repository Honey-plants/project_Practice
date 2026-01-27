import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { apiFetch, getAccessToken, setAccessToken } from "common/api/apiFetch";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [accessToken, setToken] = useState(() => getAccessToken());
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);

  // same-tab + multi-tab sync
  useEffect(() => {
    const sync = () => setToken(getAccessToken());
    window.addEventListener("auth-changed", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("auth-changed", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  // load /auth/me whenever token changes
  useEffect(() => {
    let ignore = false;

    (async () => {
      setLoading(true);
      try {
        const token = getAccessToken();
        if (!token) {
          if (!ignore) setMe(null);
          return;
        }

        const res = await apiFetch("/auth/me");
        if (!res.ok) throw new Error("me fetch failed");
        const data = await res.json();
        if (!ignore) setMe(data);
      } catch {
        setAccessToken(null);
        if (!ignore) setMe(null);
      } finally {
        if (!ignore) setLoading(false);
      }
    })();

    return () => { ignore = true; };
  }, [accessToken]);

const login = async (email, password) => {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  const base = process.env.REACT_APP_API_BASE_URL || "";
  const res = await fetch(base + "/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
    credentials: "include",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || `Login failed (${res.status})`);
  }

  const tokenData = await res.json();
  if (!tokenData?.access_token) throw new Error("No access token.");

  // ✅ 이것만 하면 됨
  setAccessToken(tokenData.access_token);   // 내부에서 auth-changed까지 쏨
//   setToken(tokenData.access_token);

  // ✅ me 호출 삭제 (useEffect가 처리)
  return true;
};

  const logout = async () => {
    try {
      await apiFetch("/auth/logout", { method: "POST" }).catch(() => {});
    } finally {


        // test 완료
//       // 현재 혼재되어 있을 수 있으니 둘 다 제거 (정리)
//       sessionStorage.removeItem("access_token");
//       localStorage.removeItem("access_token");
//       localStorage.removeItem("refresh_token"); // 원래 HttpOnly면 없어야 정상

      setAccessToken(null);
      setToken(null);
      setMe(null);
    }
  };

  const value = useMemo(() => ({
    loading,
    isLoggedIn: !!accessToken,
    accessToken,
    me,
    login,
    logout,
  }), [loading, accessToken, me]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
