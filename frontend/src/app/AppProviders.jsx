import React from "react";

import { AuthProvider } from "../context/AuthContext";
import { MemberProvider } from "../context/MemberContext";
import { UploadProvider } from "../context/UploadContext";
import { CommunityProvider } from "../context/CommunityContext";
import { ReviewProvider } from "../context/ReviewContext";

export default function AppProviders({ children }) {
  return (
    <AuthProvider>
      <MemberProvider>
        <UploadProvider>
          <CommunityProvider>
            <ReviewProvider>{children}</ReviewProvider>
          </CommunityProvider>
        </UploadProvider>
      </MemberProvider>
    </AuthProvider>
  );
}