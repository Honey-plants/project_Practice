import api from "./axiosInstance";

/**
 * 메뉴 이미지 업로드
 * POST /menu/upload
 * multipart/form-data
 */
export const menuUploadAPI = {
  upload: (formData) =>
    api.post("/menu/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }),
};
