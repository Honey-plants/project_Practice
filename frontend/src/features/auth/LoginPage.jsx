import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "providers/AuthProvider";
import "./LoginPage.css";

export default function LoginPage() {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onChange = (e) =>
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (!form.email || !form.password) {
        throw new Error("Please enter email and password.");
      }

      await login(form.email, form.password);
      navigate("/");
    } catch (err) {
      setError(err?.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="pageCenter">
      <div className="loginBox">
        <form onSubmit={onSubmit} className="loginForm">
          <label className="field">
            Email
            <input
              name="email"
              value={form.email}
              onChange={onChange}
              placeholder="example@email.com"
              autoComplete="email"
            />
          </label>

          <label className="field">
            Password
            <input
              name="password"
              type="password"
              value={form.password}
              onChange={onChange}
              placeholder="Password"
              autoComplete="current-password"
            />
          </label>

          {error && <div className="errorBox">{error}</div>}

          <button className="loginBtn wide" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>

          <button
            type="button"
            className="signupBtn wide"
            onClick={() => navigate("/signup")}
            disabled={loading}
          >
            Sign Up
          </button>
        </form>
      </div>
    </div>
  );
}
