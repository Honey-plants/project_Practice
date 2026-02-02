import React, { useState } from "react";
import PolygonOverlay from "./PolygonOverlay";
import MenuDetailModal from "./MenuDetailModal";

export default function ResultPage({ result }) {
  const [selectedItem, setSelectedItem] = useState(null);
  const [imgSize, setImgSize] = useState({ w: 0, h: 0 });

  const items = result?.items || [];
  const imageUrl = result?.result_image_url;

  if (!result) {
    return <div>결과 데이터가 없습니다.</div>;
  }

  return (
    <div className="result-page">
      {/* ✅ 반드시 relative */}
      <div style={{ position: "relative", width: "100%" }}>
        <img
          src={imageUrl}
          alt="result"
          style={{ width: "100%", display: "block" }}
          onLoad={(e) => {
            setImgSize({
              w: e.currentTarget.naturalWidth,
              h: e.currentTarget.naturalHeight,
            });
          }}
        />

        {/* ✅ overlay */}
        <PolygonOverlay
          items={items}
          imgSize={imgSize}
          onSelectItem={(item) => setSelectedItem(item)}
        />
      </div>

      {/* 모달 */}
      {selectedItem && (
        <MenuDetailModal
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
        />
      )}
    </div>
  );
}
