import api from "./axiosInstance";

export const MetaAPI = {
  // ✅ Register/Review/Profile/Edit에서 쓰는 active-only 목록
  getActiveRestrictions: () => api.get("/meta/restrictions", { params: { only_active: 1 } }),
};
