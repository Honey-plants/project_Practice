import React, { useContext } from "react";
import { useNavigate, Link } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext";
import { MemberContext } from "../../context/MemberContext";
import styles from "./Header.module.css";

/* ── 로그아웃 아이콘 (문 + 화살표) ── */
const LogoutIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"
      stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
    <polyline points="16,17 21,12 16,7"
      stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"/>
    <line x1="21" y1="12" x2="9" y2="12"
      stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"/>
  </svg>
);


export default function Header() {
  const nav = useNavigate();

  const { stateAuth, authActions } = useContext(AuthContext);
  const { stateMember } = useContext(MemberContext);

  const handleLogout = async () => {
    await authActions.logout();
    nav("/");
  };

  return (
    <div className={styles.headerWrapper}>
      <div className={styles.header}>
        {/* 왼쪽: Food Ray 로고 (클릭시 홈) */}
        <Link to="/" className={styles.logo}>Food Ray</Link>

        {/* 오른쪽: 닉네임 + 로그아웃 / 로그인 링크 */}
        <div className={styles.auth}>
          {stateAuth.accessToken ? (
            <>
              <Link to="/member/profile" className={styles.meLink}>
                {stateMember.me?.nickname || stateMember.me?.email || "me"}
              </Link>
              <button onClick={handleLogout} className={styles.logoutBtn} aria-label="로그아웃">
                <LogoutIcon />
              </button>
            </>
          ) : (
            <Link to="/login" className={styles.loginLink}>Login</Link>
          )}
        </div>
      </div>
    </div>
  );
}