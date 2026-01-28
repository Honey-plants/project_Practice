import api from "./axiosInstance";

export const UploadAPI = {
  upload: (formData) =>
    api.post("/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    }),
};