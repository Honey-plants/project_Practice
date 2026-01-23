import React, { useEffect, useState } from "react";
// import Header from "common/components/Header/Header";
import { apiFetch } from "common/api/apiFetch";

export default function MainPage() {
  const [me, setMe] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    let alive = true;

    async function loadMe() {
      setErr("");
      try {
        const res = await apiFetch("/auth/me");
        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data?.detail || `me 조회 실패 (${res.status})`);
        }
        const data = await res.json();
        if (alive) setMe(data);
      } catch (e) {
        if (alive) {
          setMe(null);
          setErr(e.message || "me 조회 실패");
        }
      }
    }

    loadMe();
    return () => {
      alive = false;
    };
  }, []);

  return (
    <>
{/*       <Header /> */}

      <div style={{ padding: 16 }}>
        <h2>TEST MAIN</h2>

        <div style={{ marginTop: 12, padding: 12, border: "1px solid #eee", borderRadius: 12 }}>
          <div style={{ fontWeight: 700, marginBottom: 8 }}>/auth/me 결과</div>

          {err ? (
            <p style={{ color: "crimson", margin: 0 }}>{err}</p>
          ) : me ? (
            <pre style={{ margin: 0, whiteSpace: "pre-wrap" }}>{JSON.stringify(me, null, 2)}</pre>
          ) : (
            <p style={{ margin: 0 }}>로딩중...</p>
          )}
        </div>

        <p style={{ marginTop: 16, color: "#666" }}>
          - 로그인 성공 후 이 페이지로 오면 /auth/me가 정상적으로 찍혀야 해.<br />
          - 로그아웃 후엔 다시 /login으로 이동하고, 쿠키/세션 정리 확인하면 됨.
        </p>
      </div>
    </>
  );
}