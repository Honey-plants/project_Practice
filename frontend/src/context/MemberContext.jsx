import React, { createContext, useContext, useEffect, useReducer } from "react";
import { MemberAPI } from "../api/memberApi";
import { AuthContext } from "./AuthContext";

export const MemberContext = createContext(null);

const initial = {
  me: null,
  loading: false,
  error: "",
};

function reducer(state, action) {
  switch (action.type) {
    case "LOADING":
      return { ...state, loading: true, error: "" };
    case "SET_ME":
      return { ...state, me: action.payload, loading: false, error: "" };
    case "ERROR":
      return { ...state, loading: false, error: action.payload || "error" };
    case "CLEAR":
      return { ...initial };
    default:
      return state;
  }
}

export function MemberProvider({ children }) {
  const { stateAuth } = useContext(AuthContext);
  const [stateMember, dispatch] = useReducer(reducer, initial);

  const memberActions = {
    loadMe: async () => {
      dispatch({ type: "LOADING" });
      try {
        const r = await MemberAPI.me();
        dispatch({ type: "SET_ME", payload: r.data });
        return r.data;
      } catch (e) {
        dispatch({ type: "ERROR", payload: e.message });
        return null;
      }
    },

    updateMe: async (payload) => {
      dispatch({ type: "LOADING" });
      try {
        await MemberAPI.updateMe(payload);
        return await memberActions.loadMe();
      } catch (e) {
        dispatch({ type: "ERROR", payload: e.message });
        throw e;
      }
    },

    clear: () => dispatch({ type: "CLEAR" }),
  };

  useEffect(() => {
    if (stateAuth.accessToken) memberActions.loadMe();
    else memberActions.clear();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stateAuth.accessToken]);

  return (
    <MemberContext.Provider value={{ stateMember, memberActions }}>
      {children}
    </MemberContext.Provider>
  );
}