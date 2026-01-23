import React from "react";
import { BrowserRouter } from "react-router-dom";

import { AuthProvider } from "providers/AuthProvider";
import AppRouter from "router/AppRouter";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </AuthProvider>
  );
}