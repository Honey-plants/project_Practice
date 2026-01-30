import api from "./axiosInstance";

export const UploadAPI = {

  upload: (formData) => api.post("/menu/upload", formData),

};