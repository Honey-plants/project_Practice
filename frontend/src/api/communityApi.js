import api from "./axiosInstance";

export const CommunityAPI = {
  // 전체: active만
  list: () => api.get("/community"),

  // 내것: active 상관없이
  myList: () => api.get("/community/me"),

  detail: (id) => api.get(`/community/${id}`),
  create: (payload) => api.post("/community", payload),
  update: (id, payload) => api.put(`/community/${id}`, payload),
};
