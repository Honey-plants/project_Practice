import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
} from "react";
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

  // ✅ 중복 호출 방지
  // - StrictMode/재마운트
  // - 토큰 세팅 타이밍 겹침
  // - 다른 화면에서 loadMe를 추가로 부르는 경우
  const lastTokenRef = useRef(null);
  const inflightRef = useRef(null);

  const memberActions = useMemo(() => {
    const loadMe = async () => {
      dispatch({ type: "LOADING" });
      try {
        const r = await MemberAPI.me();
        dispatch({ type: "SET_ME", payload: r.data });
        return r.data;
      } catch (e) {
        dispatch({ type: "ERROR", payload: e.message });
        return null;
      }
    };

    const updateMe = async (payload) => {
      dispatch({ type: "LOADING" });
      try {
        await MemberAPI.updateMe(payload);
        return await loadMe(); // ✅ update 후 me 최신화는 여기서 1회만
      } catch (e) {
        dispatch({ type: "ERROR", payload: e.message });
        throw e;
      }
    };

    const clear = () => dispatch({ type: "CLEAR" });

    return { loadMe, updateMe, clear };
  }, []);

  useEffect(() => {
    const token = stateAuth?.accessToken;

    // 토큰 없으면 초기화
    if (!token) {
      lastTokenRef.current = null;
      inflightRef.current = null;
      memberActions.clear();
      return;
    }

    // ✅ 동일 토큰으로는 다시 호출하지 않음
    if (lastTokenRef.current === token) return;

    // ✅ 이미 loadMe 진행 중이면 중복 호출 금지
    if (inflightRef.current) return;

    lastTokenRef.current = token;
    inflightRef.current = (async () => {
      try {
        await memberActions.loadMe();
      } finally {
        inflightRef.current = null;
      }
    })();
  }, [stateAuth?.accessToken, memberActions]);

  return (
    <MemberContext.Provider value={{ stateMember, memberActions }}>
      {children}
    </MemberContext.Provider>
  );
}
