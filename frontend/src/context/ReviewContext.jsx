import React, { createContext, useReducer } from "react";
import { ReviewAPI } from "../api/reviewApi";

export const ReviewContext = createContext(null);

const initial = {
  list: [],
  detail: null,
  loading: false,
  error: "",
};

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

export function ReviewProvider({ children }) {
  const [stateReview, dispatch] = useReducer(reducer, initial);

  const reviewActions = {
    fetchList: async () => {
      dispatch({ type: "LOADING" });
      try {
        const r = await ReviewAPI.list();
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
        const r = await ReviewAPI.detail(id);
        dispatch({ type: "SET_DETAIL", payload: r.data });
        return r.data;
      } catch (e) {
        dispatch({ type: "ERROR", payload: e.message });
        return null;
      }
    },

    create: async (payload) => (await ReviewAPI.create(payload)).data,
    update: async (id, payload) => (await ReviewAPI.update(id, payload)).data,
    remove: async (id) => (await ReviewAPI.remove(id)).data,
  };

  return (
    <ReviewContext.Provider value={{ stateReview, reviewActions }}>
      {children}
    </ReviewContext.Provider>
  );
}