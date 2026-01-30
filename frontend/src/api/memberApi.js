import api from "./axiosInstance";

export const MemberAPI = {

  me: async () => {
    // /member/me 우선, 없으면 /members/me fallback
    try {
      return await api.get("/member/me");
    } catch (e) {
      // axios에서 404는 메시지에 안 들어올 수 있어서 response status도 체크
      if (e?.response?.status === 404) return await api.get("/members/me");
      throw e;
    }
  },
  updateMe: (payload) => api.patch("/member/me", payload),

  register: (payload) => api.post("/member", payload),

//  getCategoriesWithItems: () => api.get("/member/categories-with-items"),
};