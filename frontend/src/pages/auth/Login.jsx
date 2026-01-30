import React, { useContext, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext";
import { MemberContext } from "../../context/MemberContext";
import "../../styles/Register.css";

export default function Login() {
  const { authActions } = useContext(AuthContext);
  const { memberActions } = useContext(MemberContext);
  const nav = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((p) => ({ ...p, [name]: value }));
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!form.email.trim() || !form.password) {
      setError("Please enter your email and password.");
      return;
    }

    setLoading(true);
    try {
      const ok = await authActions.login(form.email.trim(), form.password);
      if (ok) {
        const me = await memberActions.loadMe();
        if (me?.role === "ADMIN") {
          nav("/admin");
        } else {
          nav("/");
        }
      } else {
        setError("Login failed");
      }
    } catch (e2) {
      setError(e2.message || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="RegisterPage">
      <div className="RegisterHeader">
        <h2>Login</h2>
      </div>

      {error && <div className="RegisterMsg err">{error}</div>}

      <form className="card RegisterForm" onSubmit={onSubmit}>
        <div className="row">
          <label>Email</label>
          <input
            name="email"
            value={form.email}
            onChange={onChange}
            placeholder="email@example.com"
            autoComplete="email"
          />
        </div>

        <div className="row">
          <label>Password</label>
          <input
            name="password"
            value={form.password}
            onChange={onChange}
            type="password"
            placeholder="password"
            autoComplete="current-password"
          />
        </div>

        <div className="RegisterActions">
          <button type="submit" disabled={loading}>
            {loading ? "Logging in..." : "Login"}
          </button>
        </div>
      </form>
    </div>
  );
}