import api from "./axiosInstance";

export const AuthAPI = {
  // FastAPI OAuth2PasswordRequestForm 대응 (422 해결)
  login: (email, password) => {
    const form = new URLSearchParams();
    form.append("username", email);   // FastAPI 폼은 보통 username 키를 기대
    form.append("password", password);

    return api.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },

  logout: () => api.post("/auth/logout"),

  refresh: async () => {
    try {
      return await api.post("/auth/refresh");
    } catch (e) {
      if (e?.response?.status === 401) return null;
      throw e;
    }
  },
};