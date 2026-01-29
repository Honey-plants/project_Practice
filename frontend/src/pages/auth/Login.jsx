import React, { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext";

export default function Login() {
  const { authActions } = useContext(AuthContext);
  const nav = useNavigate();

  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const ok = await authActions.login(email, pw);
      if (ok) nav("/");
      nav("/"); // 현재는 메인페이지로 이동
//       nav("/member/profile");
    } catch (e2) {
      setError(e2.message || "로그인 실패");
    }
  };
  
  return (
    <div style={{ padding: 16, maxWidth: 420 }}>
      <h2>Login</h2>

      <form onSubmit={onSubmit} style={{ display: "grid", gap: 10 }}>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
        <input
          value={pw}
          onChange={(e) => setPw(e.target.value)}
          placeholder="password"
          type="password"
        />
        <button type="submit">Login</button>
      </form>

      {error && <div className="errorBox">{error}</div>}
    </div>
  );
}