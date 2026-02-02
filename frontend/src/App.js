import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import AppProviders from "./app/AppProviders";
import Header from "./components/layout/Header";
import ProtectedRoute from "./components/common/ProtectedRoute";

import Home from "./pages/Home";
import Login from "./pages/auth/Login";

import Profile from "./pages/member/Profile";
import EditProfile from "./pages/member/EditProfile";

import CommunityList from "./pages/community/CommunityList";
import CommunityDetail from "./pages/community/CommunityDetail";
import CommunityCreate from "./pages/community/CommunityCreate";
import CommunityEdit from "./pages/community/CommunityEdit";

import ReviewList from "./pages/review/ReviewList";
import ReviewDetail from "./pages/review/ReviewDetail";
import ReviewCreate from "./pages/review/ReviewCreate";
import ReviewEdit from "./pages/review/ReviewEdit";

import UploadTest from "./pages/upload/UploadTest";

import Register from "./pages/auth/Register";

// admin 추가
import Admin from "./pages/admin/Admin_new";

export default function App() {
  return (
    <AppProviders>
      <BrowserRouter>
        <Header />

        <Routes>
          {/* 공개 페이지 (로그인 불필요) */}
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* 커뮤니티 - 목록/상세 공개 */}
          <Route path="/community" element={<CommunityList />} />
          <Route path="/community/:id" element={<CommunityDetail />} />

          {/* 리뷰 - 목록/상세 공개 */}
          <Route path="/review" element={<ReviewList />} />
          <Route path="/review/:id" element={<ReviewDetail />} />

          {/* 관리자 페이지 */}
          <Route
            path="/admin"
            element={
              <ProtectedRoute roles={["ADMIN"]}>
                <Admin />
              </ProtectedRoute>
            }
          />

          {/* 비공개 페이지 (로그인 필수) */}
          {/* member */}
          <Route
            path="/member/profile"
            element={
              <ProtectedRoute excludeRoles={["ADMIN"]}>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/member/edit"
            element={
              <ProtectedRoute excludeRoles={["ADMIN"]}>
                <EditProfile />
              </ProtectedRoute>
            }
          />

          {/* community - 작성/수정은 로그인 필수 */}
          <Route
            path="/community/new"
            element={
              <ProtectedRoute excludeRoles={["ADMIN"]}>
                <CommunityCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="/community/:id/edit"
            element={
              <ProtectedRoute excludeRoles={["ADMIN"]}>
                <CommunityEdit />
              </ProtectedRoute>
            }
          />

          {/* review - 작성/수정은 로그인 필수 */}
          <Route
            path="/review/new"
            element={
              <ProtectedRoute excludeRoles={["ADMIN"]}>
                <ReviewCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review/:id/edit"
            element={
              <ProtectedRoute excludeRoles={["ADMIN"]}>
                <ReviewEdit />
              </ProtectedRoute>
            }
          />

          {/* upload */}
          <Route
            path="/upload/test"
            element={
              <ProtectedRoute excludeRoles={["ADMIN"]}>
                <UploadTest />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AppProviders>
  );
}