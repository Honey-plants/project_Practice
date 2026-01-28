import api from "./axiosInstance";

export const ReviewAPI = {
  list: () => api.get("/review"),
  detail: (id) => api.get(`/review/${id}`),
  create: (payload) => api.post("/review", payload),
  update: (id, payload) => api.put(`/review/${id}`, payload),
  remove: (id) => api.delete(`/review/${id}`),
};