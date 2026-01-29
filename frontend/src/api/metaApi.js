import api from "./axiosInstance";

export const MetaAPI = {
  /**
   * GET /meta/restrictions
   * - 서버가 ETag를 내려주면 저장하고
   * - 다음 호출 때 If-None-Match로 304면 캐시를 그대로 씀
   */
  async getRestrictions({ etag, onlyActive = true } = {}) {
    const res = await api.get("/meta/restrictions", {
      params: { only_active: onlyActive ? 1 : 0 },
      headers: etag ? { "If-None-Match": etag } : {},
      validateStatus: (s) => (s >= 200 && s < 300) || s === 304,
    });

    // axios는 headers 키가 소문자로 들어오는 경우가 많음
    const nextEtag = res.headers?.etag || res.headers?.ETag;

    return {
      status: res.status,         // 200 or 304
      data: res.data,             // 200일 때만 의미있음
      etag: nextEtag || etag,      // 304면 기존 etag 유지
    };
  },
};