import api from "./axiosInstance";

export const MenuAPI = {
  uploadMenu: (file) => {
    const fd = new FormData();
    fd.append("type", "menu");
    fd.append("file", file);

    return api.post("/menu/upload", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
};
