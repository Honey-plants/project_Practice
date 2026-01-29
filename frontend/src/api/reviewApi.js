import api from "./axiosInstance";

export const ReviewAPI = {
  list: () => api.get("/review"),
  detail: (id) => api.get(`/review/${id}`),
  create: (payload) => api.post("/review", payload),
  update: (id, payload) => api.put(`/review/${id}`, payload),
  remove: (id) => api.delete(`/review/${id}`),
};

// =========================
// ✅ 영수증 업로드 및 OCR 관련 API
// =========================

/**
 * uploadReceipt - 영수증 이미지를 업로드하고 OCR 결과를 받아옴
 *
 * 🔧 API 연동 시 변경 포인트:
 * 1. backend/app/features/review/router.py에서 영수증 OCR 엔드포인트가 완성되면
 * 2. 아래 URL을 실제 엔드포인트로 변경 (예: "/review/upload" 또는 "/review/receipt")
 * 3. FormData로 이미지 파일을 전송하고, OCR 결과를 응답으로 받음
 *
 * 예상 응답 형식:
 * {
 *   store_name: "가게 이름",
 *   store_en: "Store Name EN",
 *   address: "주소",
 *   menu_name: "메뉴명 리스트"
 * }
 *
 * @param {File} file - 영수증 이미지 파일
 * @returns {Promise} OCR 결과 데이터
 */
export async function uploadReceipt(file) {
  const formData = new FormData();
  formData.append("image", file);
  // 🔧 API 연동 시: type 파라미터가 필요한 경우 추가
  formData.append("type", "review");

  // 🔧 API 연동 시 변경:
  // - 현재는 "/review/upload"로 설정했지만,
  // - 실제 backend의 엔드포인트가 다르면 여기를 수정하세요
  // - 예: "/review/receipt-ocr" 등
  const response = await api.post("/review/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  // 🔧 API 연동 시 변경:
  // - 백엔드 응답 구조에 맞게 데이터 추출 로직 조정
  // - 예: response.data.ocr_result 또는 response.data 직접 사용
  return response.data;
}

// =========================
// ✅ 리뷰 이미지 업로드 API
// =========================

/**
 * uploadReviewImages - 리뷰 작성 시 첨부 이미지 업로드 (0~3개)
 *
 * 🔧 API 연동 시 변경 포인트:
 * 1. backend/app/features/review/router.py에서 리뷰 이미지 업로드 엔드포인트가 완성되면
 * 2. 아래 URL을 실제 엔드포인트로 변경 (예: "/review/{reviewId}/images")
 * 3. FormData로 여러 이미지 파일을 전송
 *
 * @param {number} reviewId - 리뷰 ID
 * @param {File[]} files - 이미지 파일 배열 (최대 3개)
 * @returns {Promise} 업로드 결과
 */
export async function uploadReviewImages(reviewId, files) {
  const formData = new FormData();

  // 여러 이미지를 FormData에 추가
  // 🔧 API 연동 시: 백엔드가 기대하는 필드명으로 변경 필요
  // - 현재는 "images" 필드명 사용
  // - 백엔드가 "image" 또는 "files" 등을 기대한다면 여기를 수정
  files.forEach((file, index) => {
    formData.append("images", file);
    // 또는 인덱스별로: formData.append(`image_${index}`, file);
  });

  // 🔧 API 연동 시 변경:
  // - 현재는 "/review/{reviewId}/images"로 설정
  // - 실제 backend의 엔드포인트가 다르면 여기를 수정하세요
  const response = await api.post(`/review/${reviewId}/images`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
}