import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "providers/AuthProvider";

export default function ProtectedRoute({ children }) {
  const { isLoggedIn, loading } = useAuth();

  if (loading) return null; // 필요하면 로딩 컴포넌트로 교체
  if (!isLoggedIn) return <Navigate to="/login" replace />;

  return children;
}