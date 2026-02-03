import React, { useMemo, useState } from "react";
import PolygonOverlay from "./PolygonOverlay";
import MenuDetailModal from "./MenuDetailModal";

/**
 * 백엔드 응답 형태 방어적 표준화
 * - router response_model: { job_id, upload_type, result }
 * - result 내부: { final, rectified_image: { mime, base64 }, run_id }
 */
function normalizeBackendPayload(raw) {
  const root = raw?.data ?? raw;

  // router wrapper가 있으면 result로 들어감
  const payload = root?.result ?? root;

  // final_translated.json (최종 결과)
  const finalObj = payload?.final ?? payload?.final_obj ?? payload?.final_json ?? payload;

  // rectified 이미지(base64)
  const rectified = payload?.rectified_image ?? payload?.rectified ?? null;
  const base64 = rectified?.base64 ?? null;
  const mime = rectified?.mime ?? "image/jpeg";
  const imageDataUrl = base64 ? `data:${mime};base64,${base64}` : null;

  const runId = payload?.run_id ?? root?.job_id ?? root?.run_id ?? null;

  return { raw: root, payload, final: finalObj, imageDataUrl, runId };
}

export default function ResultPage({ result }) {
  const [selectedItem, setSelectedItem] = useState(null);
  const [imgSize, setImgSize] = useState({ w: 0, h: 0 });
  const [imgBroken, setImgBroken] = useState(false);

  const normalized = useMemo(() => normalizeBackendPayload(result), [result]);

  // ✅ items: root.items가 없으면 final.items를 사용
  const items = result?.items || normalized?.final?.items || [];

  // ✅ image: URL이 없거나 정적서빙이 안 되면 base64(data url) 사용
  const imageUrl = result?.result_image_url || normalized?.imageDataUrl;
  const resolvedImageSrc = !imgBroken ? imageUrl : (normalized?.imageDataUrl || imageUrl);

  const jsonText = (() => {
    try {
      return JSON.stringify(result ?? {}, null, 2);
    } catch (e) {
      return String(result);
    }
  })();

  // ✅ overlay 활성화
  const TEST_TEXT_ONLY = false;

  const getItemLabel = (item) =>
    item?.menu?.menu_name_en || item?.menu?.menu_name_ko || item?.menu_name_en || item?.menu_name_ko || "(no name)";

  return (
    <div className="result-page">
      <div style={{ position: "relative", width: "100%" }}>
        {resolvedImageSrc ? (
          <img
            src={resolvedImageSrc}
            alt="result"
            style={{ width: "100%", display: "block" }}
            onLoad={(e) => {
              const w = e.currentTarget.naturalWidth || 0;
              const h = e.currentTarget.naturalHeight || 0;
              setImgSize({ w, h });
            }}
            onError={() => {
              setImgBroken(true);
              console.error("IMG_LOAD_FAIL:", imageUrl);
            }}
          />
        ) : (
          <p>AI result image will appear here.</p>
        )}

        {!TEST_TEXT_ONLY && (
          <PolygonOverlay
            items={items}
            imgSize={imgSize}
            onSelectItem={(item) => setSelectedItem(item)}
          />
        )}
      </div>

      {!TEST_TEXT_ONLY && selectedItem && (
        <MenuDetailModal item={selectedItem} onClose={() => setSelectedItem(null)} />
      )}

      {/* ✅ 메뉴별 버튼 목록 (요청: ResultPage에서 버튼 눌러 모달 열기) */}
      {!TEST_TEXT_ONLY && Array.isArray(items) && items.length > 0 && (
        <div style={{ marginTop: 14 }}>
          <h3 style={{ margin: "8px 0" }}>Detected menus</h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: 10,
            }}
          >
            {items.map((it, idx) => (
              <div
                key={it?.id || it?.item_id || idx}
                style={{
                  border: "1px solid #e6e6e6",
                  borderRadius: 10,
                  padding: 12,
                  background: "#fff",
                }}
              >
                <div style={{ fontWeight: 700, marginBottom: 8 }}>{getItemLabel(it)}</div>
                <button onClick={() => setSelectedItem(it)} style={{ width: "100%" }}>
                  View English details
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* JSON 텍스트는 유지 */}
      <div style={{ marginTop: 16 }}>
        <h3 style={{ margin: "8px 0" }}>Result JSON (text only)</h3>
        <pre
          style={{
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            background: "#f6f8fa",
            border: "1px solid #ddd",
            borderRadius: 8,
            padding: 12,
            margin: 0,
          }}
        >
          {jsonText}
        </pre>
      </div>
    </div>
  );
}
