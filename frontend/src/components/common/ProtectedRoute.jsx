import React, { useContext } from "react";
import { Navigate } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext";
import { MemberContext } from "../../context/MemberContext";

/**
 * ProtectedRoute
 * - 로그인 필요
 * - roles 옵션이 있으면 role 체크
 */
export default function ProtectedRoute({ children, roles }) {
  const { stateAuth } = useContext(AuthContext);
  const { stateMember } = useContext(MemberContext);

  if (stateAuth.loading) return <div style={{ padding: 16 }}>Loading...</div>;
  if (!stateAuth.accessToken) return <Navigate to="/login" replace />;

  // roles 체크가 필요한 경우
  if (Array.isArray(roles) && roles.length > 0) {
    if (stateMember.loading) return <div style={{ padding: 16 }}>Loading role...</div>;

    const myRole = stateMember.me?.role;
    if (!myRole || !roles.includes(myRole)) {
      return <Navigate to="/" replace />;
    }
  }

  return children;
}
