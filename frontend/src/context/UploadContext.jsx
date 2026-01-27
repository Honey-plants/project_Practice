import React, { createContext, useReducer } from "react";
import { UploadAPI } from "../api/uploadApi";

export const UploadContext = createContext(null);

const initial = {
  lastResult: null,
  uploading: false,
  error: "",
};

function reducer(state, action) {
  switch (action.type) {
    case "UPLOADING":
      return { ...state, uploading: true, error: "" };
    case "DONE":
      return { ...state, uploading: false, lastResult: action.payload, error: "" };
    case "ERROR":
      return { ...state, uploading: false, error: action.payload || "error" };
    default:
      return state;
  }
}

export function UploadProvider({ children }) {
  const [stateUpload, dispatch] = useReducer(reducer, initial);

  const uploadActions = {
    upload: async ({ file, type, owner_id }) => {
      dispatch({ type: "UPLOADING" });
      try {
        const fd = new FormData();
        fd.append("file", file);
        fd.append("type", type); // review/community/member
        if (owner_id != null) fd.append("owner_id", String(owner_id));

        const r = await UploadAPI.upload(fd);
        dispatch({ type: "DONE", payload: r.data });
        return r.data;
      } catch (e) {
        dispatch({ type: "ERROR", payload: e.message });
        throw e;
      }
    },
  };

  return (
    <UploadContext.Provider value={{ stateUpload, uploadActions }}>
      {children}
    </UploadContext.Provider>
  );
}