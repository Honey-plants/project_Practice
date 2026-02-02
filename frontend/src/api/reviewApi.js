import api from "./axiosInstance";

export const ReviewAPI = {
  //  영수증 검증
  verifyReceipt: (file) => {
    const fd = new FormData();
    fd.append("type", "receipt");
    fd.append("file", file);

    console.log("fd")

    return api.post("/review/receipt/verify", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  //  리뷰 생성(영수증 receipt_id 기반)
  createFromReceipt: ({ receipt_id, title, content, rating, images }) => {
    const fd = new FormData();
    fd.append("receipt_id", receipt_id);
    fd.append("title", title);
    fd.append("content", content);
    fd.append("rating", String(rating));

    (images || []).forEach((img) => fd.append("images", img));

    return api.post("/review/create", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },

  //  리뷰 리스트
  list: () => api.get("/review"),

  //  리뷰 상세
  detail: (id) => api.get(`/review/${id}`),

  //  리뷰 내용만 수정
  updateContent: (id, review_content) =>
    api.patch(`/review/${id}`, { review_content }),

  // (기존 list/detail 있으면 유지)
};
