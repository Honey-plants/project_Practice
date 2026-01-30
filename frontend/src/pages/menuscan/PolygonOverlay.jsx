import React from "react";

/**
 * items: AI JSON items[]
 * - item.match.poly: [[x,y], ...]
 */
export default function PolygonOverlay({ items, onSelectItem }) {
  return (
    <>
      {items.map((item, idx) => {
        const poly = item?.match?.poly;
        if (!Array.isArray(poly)) return null;

        const points = poly.map((p) => p.join(",")).join(" ");

        return (
          <svg
            key={idx}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              width: "100%",
              height: "100%",
              pointerEvents: "none",
            }}
          >
            <polygon
              points={points}
              fill="rgba(255, 0, 0, 0.25)"
              stroke="red"
              strokeWidth="2"
              style={{ pointerEvents: "auto", cursor: "pointer" }}
              onClick={() => onSelectItem(item)}
            />
          </svg>
        );
      })}
    </>
  );
}
