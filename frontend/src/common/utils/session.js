// getSession, getMemberId, getNickname
// 인증/세션 단일 소스

export const SESSION_KEY = "final_project_session";

// 메모리 캐시(리렌더/요청 중 반복 JSON.parse 방지)
let _cachedSession = null;
let _inited = false;

export function getSession() {
  if (_inited && _cachedSession) return _cachedSession;
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    _cachedSession = raw ? JSON.parse(raw) : null;
  } catch {
    _cachedSession = null;
  } finally {
    _inited = true;
  }
  return _cachedSession;
}

export function setSession(session) {
  // session: { access_token, member_id, nickname }
  _cachedSession = session || null;
  _inited = true;

  if (!session) localStorage.removeItem(SESSION_KEY);
  else localStorage.setItem(SESSION_KEY, JSON.stringify(session));

  // 같은 탭 즉시 반영
  window.dispatchEvent(new Event("session-changed"));
}

export function clearSession() {
  setSession(null);
}

export function getAccessToken() {
  return getSession()?.access_token || null;
}

export function getMemberId() {
  return getSession()?.member_id || null;
}

export function getNickname() {
  return getSession()?.nickname || "";
}

// 다른 탭(storage) + 같은 탭(session-changed) 모두 커버
export function subscribeSession(callback) {
  const handler = () => callback(getSession());
  window.addEventListener("storage", handler);
  window.addEventListener("session-changed", handler);
  return () => {
    window.removeEventListener("storage", handler);
    window.removeEventListener("session-changed", handler);
  };
}
