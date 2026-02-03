import React, { useContext } from "react";
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext";
import { MemberContext } from "../../context/MemberContext";
import "./Header.css"

export default function Header() {
  const { stateAuth, authActions } = useContext(AuthContext);
  const { stateMember } = useContext(MemberContext);
  const nav = useNavigate();

  const onLogout = async () => {
    await authActions.logout();
    nav("/login");
  };

  const isAdmin = stateMember.me?.role === "ADMIN";

  return (
    <div className="header-wrapper">
      <div className="header">
        <div className="nav">
          {isAdmin ? (
            <>
              <Link to="/admin">Admin</Link>
            </>
          ) : (
            <>
              <Link to="/">Home</Link>
              <Link to="/review">Review</Link>
              <Link to="/community">Community</Link>
            </>
          )}
        </div>

        {/* 여기(auth 영역)에 Register를 추가 */}
        <div className="auth">
          {stateAuth.accessToken ? (
            <>
              <Link to="/member/profile" className="me-link">
                {stateMember.me?.nickname || stateMember.me?.email || "me"}
              </Link>
              <button onClick={onLogout}>Logout</button>
            </>
          ) : (
            <>
              {/* 2-2번: Register 링크 추가 위치 */}
              <Link to="/register">Register</Link>
              <Link to="/login">Login</Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}