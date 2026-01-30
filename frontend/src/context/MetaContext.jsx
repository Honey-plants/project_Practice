import React, { createContext, useMemo, useReducer } from "react";
import { MetaAPI } from "../api/metaApi";

export const MetaContext = createContext(null);

const initial = {
  restrictions: [],
  loading: false,
  loaded: false,
  error: null,
};

function reducer(state, action) {
  switch (action.type) {
    case "LOAD_START":
      return { ...state, loading: true, error: null };
    case "LOAD_OK":
      return { ...state, loading: false, loaded: true, restrictions: action.payload || [] };
    case "LOAD_ERR":
      return { ...state, loading: false, error: action.error || "error" };
    case "RESET":
      return initial;
    default:
      return state;
  }
}

export function MetaProvider({ children }) {
  const [stateMeta, dispatch] = useReducer(reducer, initial);

  const metaActions = useMemo(() => {
    return {
      // ✅ active-only 캐시 로드
      loadRestrictions: async ({ force = false } = {}) => {
        if (!force && stateMeta.loaded) return;
        dispatch({ type: "LOAD_START" });
        try {
          const res = await MetaAPI.getActiveRestrictions();
          // 서버가 {meta,data:[...]}면 res.data.data
          const list = Array.isArray(res?.data?.data) ? res.data.data : (res?.data || []);
          dispatch({ type: "LOAD_OK", payload: list });
        } catch (e) {
          dispatch({ type: "LOAD_ERR", error: e?.response?.data?.detail || e?.message });
        }
      },
      refresh: async ({ force = true } = {}) => {
        return metaActions.loadRestrictions({ force });
      },
      reset: () => dispatch({ type: "RESET" }),
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stateMeta.loaded]);

  const value = useMemo(() => ({ stateMeta, metaActions }), [stateMeta, metaActions]);

  return <MetaContext.Provider value={value}>{children}</MetaContext.Provider>;
}
