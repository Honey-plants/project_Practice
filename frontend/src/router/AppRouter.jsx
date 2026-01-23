import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import RootLayout from "layouts/RootLayout";
import AuthLayout from "layouts/AuthLayout";
import ProtectedRoute from "router/ProtectedRoute";




// pages
// import HomePage from "features/main/pages/HomePage";
// import CameraPage from "features/main/pages/CameraPage";
// import PreviewPage from "features/main/pages/PreviewPage";
// import ResultPage from "features/main/pages/ResultPage";
// import UploadPage from "features/main/pages/UploadPage";

import LoginPage from "features/auth/LoginPage";
import SignupPage from "features/auth/SignupPage";
import MainPage from "features/main/MainPage";
// import ProfilePage from "features/profile/ProfilePage";
// import CommunityPage from "features/community/CommunityPage";
// import ReviewPage from "features/review/ReviewPage";
// import ReviewWritePage from "features/review/ReviewWritePage";

export default function AppRouter() {
  return (
    <Routes>
      {/* 인증 레이아웃 */}
      <Route element={<AuthLayout />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/" element={<MainPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
