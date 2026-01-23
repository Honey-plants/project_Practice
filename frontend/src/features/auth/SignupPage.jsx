import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "./SignupPage.css";

import { GENDER_OPTIONS, COUNTRY_OPTIONS } from "common/components/signupOptions";
import { apiFetch } from "common/api/apiFetch";

export default function SignupPage() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
    nickname: "",
    gender: "",
    country: "",
  });

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onChange = (e) =>
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (!form.email || !form.password || !form.nickname) {
        throw new Error("Email, Password, Nickname은 필수입니다.");
      }

      const res = await apiFetch("/members", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
        skipRefresh: true, // 회원가입은 refresh 시도 X
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err?.detail || `회원가입 실패 (${res.status})`);
      }

      alert("회원가입 완료! 로그인 해주세요.");
      navigate("/login");
    } catch (err) {
      setError(err?.message || "회원가입 실패");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pageCenter">
      <div className="signupBox">
        <form onSubmit={onSubmit} className="signupForm">
          <label className="field">
            이메일
            <input
              name="email"
              value={form.email}
              onChange={onChange}
              placeholder="example@email.com"
              autoComplete="email"
            />
          </label>

          <label className="field">
            비밀번호
            <input
              type="password"
              name="password"
              value={form.password}
              onChange={onChange}
              placeholder="비밀번호"
              autoComplete="new-password"
            />
          </label>

          <label className="field">
            닉네임
            <input
              name="nickname"
              value={form.nickname}
              onChange={onChange}
              placeholder="닉네임"
            />
          </label>

          <label className="field">
            성별
            <select name="gender" value={form.gender} onChange={onChange}>
              <option value="">선택</option>
              {GENDER_OPTIONS.map((g) => (
                <option key={g} value={g}>
                  {g}
                </option>
              ))}
            </select>
          </label>

          <label className="field">
            국가
            <select name="country" value={form.country} onChange={onChange}>
              <option value="">선택</option>
              {COUNTRY_OPTIONS.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </label>

          {error && <div className="errorBox">{error}</div>}

          <button className="signupBtn wide" disabled={loading}>
            {loading ? "가입 중..." : "회원가입"}
          </button>

          <button
            type="button"
            className="loginBtn wide"
            onClick={() => navigate("/login")}
            disabled={loading}
          >
            로그인
          </button>
        </form>
      </div>
    </div>
  );
}
