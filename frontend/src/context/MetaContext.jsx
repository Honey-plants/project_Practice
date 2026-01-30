import React, { createContext, useEffect, useMemo, useRef, useState } from "react";
import { MetaAPI } from "../api/metaApi";

export const MetaContext = createContext(null);

const LS_RESTRICTIONS = "meta_restrictions_cache_v1";
const LS_ETAG = "meta_restrictions_etag_v1";

function safeJsonParse(v, fallback) {
  try {
    return JSON.parse(v);
  } catch {
    return fallback;
  }
}

export function MetaProvider({ children }) {
  const didBoot = useRef(false);

  const [stateMeta, setStateMeta] = useState(() => {
    const cached = safeJsonParse(localStorage.getItem(LS_RESTRICTIONS), []);
    const etag = localStorage.getItem(LS_ETAG) || "";
    return {
      restrictions: Array.isArray(cached) ? cached : [],
      etag,
      loading: false,
      error: "",
      lastFetchedAt: null,
    };
  });

  const persist = (restrictions, etag) => {
    localStorage.setItem(LS_RESTRICTIONS, JSON.stringify(restrictions || []));
    if (etag) localStorage.setItem(LS_ETAG, etag);
  };

  const bootstrap = async () => {
    // 캐시가 있으면 일단 바로 보여주고, 서버 확인만 한다
    setStateMeta((p) => ({ ...p, loading: true, error: "" }));

    try {
      const { status, data, etag } = await MetaAPI.getRestrictions({
        etag: stateMeta.etag,
        onlyActive: true,
      });

      if (status === 304) {
        // 변경 없음: 캐시 유지, 로딩만 종료
        // 단, 캐시가 비어있는데 304가 오면(예: 예전 버그로 [] 저장) 강제로 한번 더 받아온다
        if (!Array.isArray(stateMeta.restrictions) || stateMeta.restrictions.length === 0) {
          const forced = await MetaAPI.getRestrictions({ etag: "", onlyActive: true });
          const forcedData = forced.data;
          const forcedNext = Array.isArray(forcedData)
            ? forcedData
            : Array.isArray(forcedData?.data)
              ? forcedData.data
              : Array.isArray(forcedData?.categories)
                ? forcedData.categories
                : [];
          persist(forcedNext, forced.etag);
          setStateMeta((p) => ({
            ...p,
            restrictions: forcedNext,
            etag: forced.etag || p.etag,
            loading: false,
            error: "",
            lastFetchedAt: Date.now(),
          }));
          return;
        }
        setStateMeta((p) => ({
          ...p,
          loading: false,
          error: "",
          etag: etag || p.etag,
          lastFetchedAt: Date.now(),
        }));
        return;
      }

      // 200: 새 데이터
      const next = Array.isArray(data)
        ? data
        : Array.isArray(data?.data)
          ? data.data
          : Array.isArray(data?.categories)
            ? data.categories
            : [];
      persist(next, etag);

      setStateMeta((p) => ({
        ...p,
        restrictions: next,
        etag: etag || p.etag,
        loading: false,
        error: "",
        lastFetchedAt: Date.now(),
      }));
    } catch (e) {
      setStateMeta((p) => ({
        ...p,
        loading: false,
        error: e?.message || "메타 데이터 로딩 실패",
      }));
    }
  };

  // 관리자가 category/item 수정했을 때, 또는 강제 새로고침 버튼에서 호출용
  const refresh = async ({ force = false } = {}) => {
    setStateMeta((p) => ({ ...p, loading: true, error: "" }));

    try {
      const { status, data, etag } = await MetaAPI.getRestrictions({
        etag: force ? "" : stateMeta.etag,
        onlyActive: true,
      });

      if (status === 304) {
        // 캐시가 비어있는데 304면 강제로 한번 더
        if (!Array.isArray(stateMeta.restrictions) || stateMeta.restrictions.length === 0) {
          const forced = await MetaAPI.getRestrictions({ etag: "", onlyActive: true });
          const forcedData = forced.data;
          const forcedNext = Array.isArray(forcedData)
            ? forcedData
            : Array.isArray(forcedData?.data)
              ? forcedData.data
              : Array.isArray(forcedData?.categories)
                ? forcedData.categories
                : [];
          persist(forcedNext, forced.etag);
          setStateMeta((p) => ({
            ...p,
            restrictions: forcedNext,
            etag: forced.etag || p.etag,
            loading: false,
            error: "",
            lastFetchedAt: Date.now(),
          }));
          return;
        }
        setStateMeta((p) => ({ ...p, loading: false, lastFetchedAt: Date.now() }));
        return;
      }

      const next = Array.isArray(data)
        ? data
        : Array.isArray(data?.data)
          ? data.data
          : Array.isArray(data?.categories)
            ? data.categories
            : [];
      persist(next, etag);

      setStateMeta((p) => ({
        ...p,
        restrictions: next,
        etag: etag || p.etag,
        loading: false,
        error: "",
        lastFetchedAt: Date.now(),
      }));
    } catch (e) {
      setStateMeta((p) => ({
        ...p,
        loading: false,
        error: e?.message || "메타 데이터 갱신 실패",
      }));
    }
  };

  useEffect(() => {
    if (didBoot.current) return;
    didBoot.current = true;
    bootstrap();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const value = useMemo(() => ({ stateMeta, metaActions: { bootstrap, refresh } }), [stateMeta]);

  return <MetaContext.Provider value={value}>{children}</MetaContext.Provider>;
}