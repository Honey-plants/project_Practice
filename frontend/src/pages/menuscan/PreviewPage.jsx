import React, { useMemo, useState } from "react";
import PolygonOverlay from "./PolygonOverlay";
import MenuDetailModal from "./MenuDetailModal";
import "./ResultPage.css";

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
    item?.menu?.menu_name_en ||
    item?.menu?.menu_name_ko ||
    item?.menu_name_en ||
    item?.menu_name_ko ||
    "(no name)";

  return (
    <div className="ms-rp__root">
      <div className="ms-rp__imageWrap">
        {resolvedImageSrc ? (
          <img
            className="ms-rp__image"
            src={resolvedImageSrc}
            alt="result"
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
          <p className="ms-rp__empty">AI result image will appear here.</p>
        )}

        {!TEST_TEXT_ONLY && (
          <PolygonOverlay items={items} imgSize={imgSize} onSelectItem={(item) => setSelectedItem(item)} />
        )}
      </div>

      {!TEST_TEXT_ONLY && selectedItem && (
        <MenuDetailModal item={selectedItem} onClose={() => setSelectedItem(null)} />
      )}

      {/* ✅ 메뉴별 버튼 목록 */}
      {!TEST_TEXT_ONLY && Array.isArray(items) && items.length > 0 && (
        <div className="ms-rp__menuSection">
          <h3 className="ms-rp__menuTitle">Detected menus</h3>

          <div className="ms-rp__menuGrid">
            {items.map((it, idx) => (
              <div className="ms-rp__menuCard" key={it?.id || it?.item_id || idx}>
                <div className="ms-rp__menuName">{getItemLabel(it)}</div>
                <button className="ms-rp__menuBtn" onClick={() => setSelectedItem(it)}>
                  View English details
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* JSON 텍스트는 유지 */}
      <div className="ms-rp__jsonWrap">
        <h3 className="ms-rp__jsonTitle">Result JSON (text only)</h3>
        <pre className="ms-rp__jsonPre">{jsonText}</pre>
      </div>
    </div>
  );
}
