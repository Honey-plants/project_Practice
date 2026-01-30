import api from "./axiosInstance";

export const RestrictionsAdminAPI = {
  // 전체 조회(onlyActive=false) or 활성만(onlyActive=true)
  list: ({ onlyActive = false } = {}) =>
    api.get(`/restrictions?only_active=${onlyActive ? 1 : 0}`),

  batchCreate: (payload) => api.post("/admin/restrictions/batch", payload),

  updateCategory: (id, payload) =>
    api.put(`/admin/restrictions/category/${id}`, payload),

  updateItem: (id, payload) =>
    api.put(`/admin/restrictions/item/${id}`, payload),
};