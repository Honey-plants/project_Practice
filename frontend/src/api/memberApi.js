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

  // 회원 탈퇴
  withdraw: async () => {
    // 백엔드가 /member/me DELETE로 구현되어 있다고 가정
    try {
      return await api.delete("/member/me");
    } catch (e) {
      // 만약 백엔드가 /members/me로 되어있으면 fallback
      if (e?.response?.status === 404) return await api.delete("/members/me");
      throw e;
    }
  },
};