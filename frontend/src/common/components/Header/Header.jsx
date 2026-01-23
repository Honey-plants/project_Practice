import React from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "providers/AuthProvider";

export default function Header() {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const onLogout = async () => {
    try {
      await logout();
      navigate("/login");
    } catch (e) {
      alert(e?.message || "로그아웃 실패");
    }
  };

  return (
    <header style={{ display: "flex", gap: 8, alignItems: "center", padding: 12, borderBottom: "1px solid #eee" }}>
      <strong style={{ marginRight: 12 }}>HEANET</strong>

      <button onClick={() => navigate("/")}>Main</button>
      <button onClick={() => navigate("/login")}>Login</button>

      <div style={{ flex: 1 }} />

      <button onClick={onLogout}>Logout</button>
    </header>
  );
}



// import React from "react";
// import { NavLink, useNavigate } from "react-router-dom";
// import "./Header.css";
// import { useAuth } from "providers/AuthProvider";
//
// export default function Header({
//   showNav = true,
//   showAuthArea = true,
//   showLogin = true,
//   showSignup = true,
// }) {
//   const navigate = useNavigate();
//   const { isLoggedIn, me, logout } = useAuth();
//
//   return (
//     <header className="appHeader">
//       <div className="headerInner">
//         <button type="button" className="brand" onClick={() => navigate("/")}>
//           FOOD RAY
//         </button>
//
//         {showNav && (
//           <nav className="nav">
//             <NavLink className="navItem" to="/review">Review</NavLink>
//             <NavLink className="navItem" to="/community">Community</NavLink>
//           </nav>
//         )}
//
//         {showAuthArea && (
//           <div className="authArea">
//             {isLoggedIn ? (
//               <>
//                 <button
//                   type="button"
//                   className="ghostBtn"
//                   onClick={() => navigate("/profile")}
//                 >
//                   {me?.nickname || "Profile"}
//                 </button>
//                 <button type="button" className="solidBtn" onClick={logout}>
//                   로그아웃
//                 </button>
//               </>
//             ) : (
//               <>
//                 {showLogin && (
//                   <button
//                     type="button"
//                     className="ghostBtn"
//                     onClick={() => navigate("/login")}
//                   >
//                     로그인
//                   </button>
//                 )}
//                 {showSignup && (
//                   <button
//                     type="button"
//                     className="solidBtn"
//                     onClick={() => navigate("/signup")}
//                   >
//                     회원가입
//                   </button>
//                 )}
//               </>
//             )}
//           </div>
//         )}
//       </div>
//     </header>
//   );
// }
