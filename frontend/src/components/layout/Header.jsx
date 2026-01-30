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
    <div className="header">
      <div className="nav">
        {isAdmin ? (
          <>
            <Link to="/admin">Admin</Link>
          </>
        ) : (
          <>
            <Link to="/">Home</Link>
            <Link to="/community">Community</Link>
            <Link to="/review">Review</Link>
            <Link to="/upload/test">UploadTest</Link>
          </>
        )}
      </div>

      {/* 여기(auth 영역)에 Register를 추가 */}
      <div className="auth">
        {stateAuth.accessToken ? (
          <>
            <span className="me">
              {stateMember.me?.nickname || stateMember.me?.email || "me"}
            </span>
            {!isAdmin && <Link to="/member/profile">Profile</Link>}
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
  );
}