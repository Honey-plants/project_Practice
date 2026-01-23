import React, { useEffect, useMemo, useState } from "react";
import { useNavigate, NavLink } from "react-router-dom";
import "./Header.css";

import { getSession, subscribeSession } from "../../utils/session";
import { logout as logoutApi } from "../../utils/authApi";

/**
 * Header
 * - 기본: localStorage의 SESSION_KEY를 읽어 로그인 UI 처리 (전 페이지 공통)
 * - 필요하면 session/isLoggedIn/onLogout를 props로 넘겨 오버라이드 가능
 */
export default function Header({
  showNav = true,
  showAuthArea = true,
  session: sessionProp,
  isLoggedIn: isLoggedInProp,
  showLogin = true,
  showSignup = true,
  onLogout,
}) {
  const navigate = useNavigate();
  const [sessionState, setSessionState] = useState(() => getSession());

  useEffect(() => {
    if (sessionProp !== undefined) return;
    return subscribeSession(setSessionState);
  }, [sessionProp]);

  const session = sessionProp !== undefined ? sessionProp : sessionState;

  const isLoggedIn = useMemo(() => {
    if (typeof isLoggedInProp === "boolean") return isLoggedInProp;
    return !!session?.access_token && !!session?.member_id;
  }, [isLoggedInProp, session]);

  const handleLogout = async () => {
    try {
      if (onLogout) await onLogout();
      else await logoutApi();
    } finally {
      navigate("/login");
    }
  };

  console.log("Header sessionProp:", sessionProp);
  console.log("Header session(final):", session);

  return (
    <header>
      <button onClick={() => navigate("/")}>FOOD RAY</button>

      {showNav && (
        <nav>
          <NavLink to="/review">Review</NavLink>
          <NavLink to="/community">Community</NavLink>
        </nav>
      )}

      {showAuthArea && (
        <div>
          {isLoggedIn ? (
            <>
              <button onClick={() => navigate(`/profile/${session?.member_id}`)}>
                {session?.nickname || "Profile"}
              </button>
              <button onClick={handleLogout}>로그아웃</button>
            </>
          ) : (
            <>
              {showLogin && <button onClick={() => navigate("/login")}>로그인</button>}
              {showSignup && <button onClick={() => navigate("/signup")}>회원가입</button>}
            </>
          )}
        </div>
      )}
    </header>
  );
}
