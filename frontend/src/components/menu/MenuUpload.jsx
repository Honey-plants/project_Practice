import React, { useMemo, useState } from "react";
import { MenuAPI } from "../../api/menuApi";
import ResultPage from "../../pages/menuscan/ResultPage"

/**
 * 백엔드 응답 형태 방어적 표준화
 * - router response_model: { job_id, upload_type, result }
 * - result 내부: { final, rectified_image: { mime, base64 }, run_id }
 */
function normalizeBackendPayload(raw) {
  const root = raw?.data ?? raw;

  // 1) router wrapper가 있으면 result로 들어감
  const payload = root?.result ?? root;

  // 2) 서비스가 반환한 형태
  const finalObj = payload?.final ?? payload?.final_obj ?? payload?.final_json ?? payload;

  // 3) rectified 이미지 추출
  const rectified = payload?.rectified_image ?? payload?.rectified ?? null;
  const base64 = rectified?.base64 ?? null;
  const mime = rectified?.mime ?? "image/jpeg";
  const imageDataUrl = base64 ? `data:${mime};base64,${base64}` : null;

  // 4) run_id / job_id
  const runId = payload?.run_id ?? root?.job_id ?? root?.run_id ?? null;

  return { raw: root, payload, final: finalObj, imageDataUrl, runId };
}

export default function MenuUploadInline() {
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState("");
  const [rawRes, setRawRes] = useState(null);
  const [loading, setLoading] = useState(false);

  const normalized = useMemo(() => (rawRes ? normalizeBackendPayload(rawRes) : null), [rawRes]);

  const onUpload = async () => {
    if (!file) return setMsg("이미지를 선택해줘");
    setMsg("");
    setRawRes(null);
    setLoading(true);

    try {
      const r = await MenuAPI.uploadMenu(file);
      setRawRes(r);
      setMsg("✅ 메뉴 분석 완료");
    } catch (e) {
      setMsg(`❌ ${e?.response?.data?.detail || e?.message || "업로드 실패"}`);
    } finally {
      setLoading(false);
    }
  };

  if (normalized) {
    // ResultPage는 "원본응답"을 그대로 받아서 내부에서 표준화하도록 구성
    return (
      <div>
        <div style={{ marginBottom: 12, display: "flex", gap: 8 }}>
          <button onClick={() => setRawRes(null)}>다시 업로드</button>
          <button onClick={() => setMsg("")}>메시지 지우기</button>
        </div>
        {msg && <div style={{ marginBottom: 12 }}>{msg}</div>}
        <ResultPage result={normalized.raw?.data ?? normalized.raw} />
      </div>
    );
  }

  return (
    <div style={{ border: "1px solid #ddd", padding: 12, borderRadius: 8 }}>
      <h3 style={{ marginTop: 0 }}>메뉴 이미지 업로드</h3>

      <input
        type="file"
        accept="image/*"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button onClick={onUpload} disabled={loading} style={{ marginLeft: 8 }}>
        {loading ? "분석중..." : "업로드/분석"}
      </button>

      {msg && <div style={{ marginTop: 10 }}>{msg}</div>}
    </div>
  );
}
