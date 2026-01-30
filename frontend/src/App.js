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
import Community from "./pages/community/Community";

import ReviewList from "./pages/review/ReviewList";
import ReviewDetail from "./pages/review/ReviewDetail";
import ReviewCreate from "./pages/review/ReviewCreate";
import ReviewEdit from "./pages/review/ReviewEdit";

import UploadTest from "./pages/upload/UploadTest";

import CameraUploadPage from "./pages/menuscan/CameraUploadPage";

import Register from "./pages/auth/Register";

// admin 추가
import Admin from "./pages/admin/Admin_new";

export default function App() {
  return (
    <AppProviders>
      <BrowserRouter>
        <Header />

        <Routes>
          <Route path="/" element={<Home />} />

          <Route path="/login" element={<Login />} />

          // Routes 안에 추가
          {/* auth */}
          <Route path="/register" element={<Register />} />
          <Route
            path="/admin"
            element={
              <ProtectedRoute roles={["ADMIN"]}>
                <Admin />
              </ProtectedRoute>
            }
          />

          {/* member */}
          <Route
            path="/member/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/member/edit"
            element={
              <ProtectedRoute>
                <EditProfile />
              </ProtectedRoute>
            }
          />

          {/* community */}
          <Route path="/community" element={<Community />} />
          <Route path="/community/:id" element={<CommunityDetail />} />
          <Route
            path="/community/new"
            element={
              <ProtectedRoute>
                <CommunityCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="/community/:id/edit"
            element={
              <ProtectedRoute>
                <CommunityEdit />
              </ProtectedRoute>
            }
          />

          {/* review */}
          <Route path="/review" element={<ReviewList />} />
          <Route path="/review/:id" element={<ReviewDetail />} />
          <Route
            path="/review/new"
            element={
              <ProtectedRoute>
                <ReviewCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="/review/:id/edit"
            element={
              <ProtectedRoute>
                <ReviewEdit />
              </ProtectedRoute>
            }
          />

          {/* upload */}
          <Route
            path="/upload/test"
            element={
              <ProtectedRoute>
                <UploadTest />
              </ProtectedRoute>
            }
          />
          <Route
            path="/menu/upload"
            element={
              <ProtectedRoute>
                <CameraUploadPage />
              </ProtectedRoute>
            }
          />



          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AppProviders>
  );
}