// src/app/AppProviders.jsx
import React from "react";

import { AuthProvider } from "../context/AuthContext";
import { MemberProvider } from "../context/MemberContext";
import { UploadProvider } from "../context/UploadContext";
import { CommunityProvider } from "../context/CommunityContext";
import { ReviewProvider } from "../context/ReviewContext";
// Category, Item 전체 리스트 조회
import { MetaProvider } from "../context/MetaContext";

export default function AppProviders({ children }) {
  return (
    <AuthProvider>
      <MetaProvider>
        <MemberProvider>
          <UploadProvider>
            <CommunityProvider>
              <ReviewProvider>{children}</ReviewProvider>
            </CommunityProvider>
          </UploadProvider>
        </MemberProvider>
      </MetaProvider>
    </AuthProvider>
  );
}