import api from "./axiosInstance";

export const CommunityAPI = {
  list: () => api.get("/community"),
  detail: (id) => api.get(`/community/${id}`),
  create: (payload) => api.post("/community", payload),
  update: (id, payload) => api.put(`/community/${id}`, payload),
  remove: (id) => api.delete(`/community/${id}`),
};