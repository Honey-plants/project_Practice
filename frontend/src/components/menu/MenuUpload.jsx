import React, { useState } from "react";
import { MenuAPI } from "../../api/menuApi";

export default function MenuUploadInline() {
  const [file, setFile] = useState(null);
  const [msg, setMsg] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const onUpload = async () => {
    if (!file) return setMsg("이미지를 선택해줘");
    setMsg("");
    setResult(null);
    setLoading(true);

    try {
      const r = await MenuAPI.uploadMenu(file);
      setResult(r.data?.result ?? r.data);
      setMsg("✅ 메뉴 분석 완료");
    } catch (e) {
      setMsg(`❌ ${e?.response?.data?.detail || e?.message || "업로드 실패"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ border: "1px solid #ddd", padding: 12, borderRadius: 8 }}>
      <h3 style={{ marginTop: 0 }}>메뉴 이미지 업로드 [MENU TEST]</h3>

      <input
        type="file"
        accept="image/*"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button onClick={onUpload} disabled={loading} style={{ marginLeft: 8 }}>
        {loading ? "분석중..." : "업로드/분석"}
      </button>

      {msg && <div style={{ marginTop: 10 }}>{msg}</div>}

      {result && (
        <pre style={{ marginTop: 12, whiteSpace: "pre-wrap", background: "#fafafa", padding: 10 }}>
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
