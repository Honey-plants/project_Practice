import React, { useState } from "react";
import PolygonOverlay from "./PolygonOverlay";
import MenuDetailModal from "./MenuDetailModal";

export default function ResultPage({ result }) {
  const [selectedItem, setSelectedItem] = useState(null);

  /**
   * AI 연동 전에도 깨지지 않도록 방어
   */
  const items = result?.items || [];
  const imageUrl = result?.result_image_url;

  // ✅ 테스트 표시용: JSON 텍스트로만 보기
  const jsonText = (() => {
    try {
      return JSON.stringify(result ?? {}, null, 2);
    } catch (e) {
      return String(result);
    }
  })();

  // ✅ 테스트 모드: 현재는 "이미지 + JSON 텍스트만" 표시
  const TEST_TEXT_ONLY = true;

  return (
    <div className="result-page" style={{ position: "relative" }}>
      {imageUrl ? (
        <img src={imageUrl} alt="result" style={{ width: "100%" }} />
      ) : (
        <p>AI result image will appear here.</p>
      )}

      {/* ✅ JSON 결과를 텍스트로만 표시 (테스트용) */}
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

      {/* 기존 UI는 테스트 동안 비활성화 (변수명/경로 유지) */}
      {!TEST_TEXT_ONLY && (
        <>
          <PolygonOverlay
            items={items}
            onSelectItem={(item) => setSelectedItem(item)}
          />

          {selectedItem && (
            <MenuDetailModal
              item={selectedItem}
              onClose={() => setSelectedItem(null)}
            />
          )}
        </>
      )}
    </div>
  );
}
