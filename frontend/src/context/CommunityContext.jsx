import React, { createContext, useReducer } from "react";
import { CommunityAPI } from "../api/communityApi";

export const CommunityContext = createContext(null);

const initial = { list: [], detail: null, loading: false, error: "" };

function reducer(state, action) {
  switch (action.type) {
    case "LOADING":
      return { ...state, loading: true, error: "" };
    case "SET_LIST":
      return { ...state, list: action.payload || [], loading: false };
    case "SET_DETAIL":
      return { ...state, detail: action.payload, loading: false };
    case "ERROR":
      return { ...state, loading: false, error: action.payload || "error" };
    default:
      return state;
  }
}

export function CommunityProvider({ children }) {
  const [stateCommunity, dispatch] = useReducer(reducer, initial);

  const communityActions = {
    // 전체: active만
    fetchList: async () => {
      dispatch({ type: "LOADING" });
      try {
        const r = await CommunityAPI.list();
        const list = Array.isArray(r.data) ? r.data : r.data?.items ?? [];
        dispatch({ type: "SET_LIST", payload: list });
        return list;
      } catch (e) {
        dispatch({ type: "ERROR", payload: e.message });
        return [];
      }
    },

    // 내것: active 상관없이 전부
    fetchMyList: async () => {
      dispatch({ type: "LOADING" });
      try {
        const r = await CommunityAPI.myList();
        const list = Array.isArray(r.data) ? r.data : r.data?.items ?? [];
        dispatch({ type: "SET_LIST", payload: list });
        return list;
      } catch (e) {
        dispatch({ type: "ERROR", payload: e.message });
        return [];
      }
    },

    fetchDetail: async (id) => {
      dispatch({ type: "LOADING" });
      try {
        const r = await CommunityAPI.detail(id);
        dispatch({ type: "SET_DETAIL", payload: r.data });
        return r.data;
      } catch (e) {
        dispatch({ type: "ERROR", payload: e.message });
        return null;
      }
    },

    create: async (payload) => (await CommunityAPI.create(payload)).data,
    update: async (id, payload) => (await CommunityAPI.update(id, payload)).data,
    remove: async (id) => (await CommunityAPI.remove(id)).data,

    // 공개/비공개 토글 후 상세 상태 갱신
    toggleActive: async (id, active) => {
      const r = await CommunityAPI.update(id, { community_active: active });
      // 로컬 detail 상태도 바로 갱신
      dispatch({ type: "SET_DETAIL", payload: { ...r.data, community_active: active } });
      return r.data;
    },

    // 좋아요(recommend) +1
    // recommend: async (id) => {
    //   const r = await CommunityAPI.recommend(id);
    //   return r.data;
    // },
  };

  return (
    <CommunityContext.Provider value={{ stateCommunity, communityActions }}>
      {children}
    </CommunityContext.Provider>
  );
}
