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

  return (
    <div className="result-page" style={{ position: "relative" }}>
      {imageUrl ? (
        <img src={imageUrl} alt="result" style={{ width: "100%" }} />
      ) : (
        <p>AI result image will appear here.</p>
      )}

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
    </div>
  );
}
