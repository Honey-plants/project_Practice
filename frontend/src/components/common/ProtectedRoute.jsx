import React, { useContext } from "react";
import { Navigate } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext";

export default function ProtectedRoute({ children }) {
  const { stateAuth } = useContext(AuthContext);
  if (stateAuth.loading) return <div style={{ padding: 16 }}>Loading...</div>;
  if (!stateAuth.accessToken) return <Navigate to="/login" replace />;
  return children;
}