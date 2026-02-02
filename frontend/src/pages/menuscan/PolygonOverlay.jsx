import React, { useMemo } from "react";

function extractPoly(item) {
  // ✅ 네 final_translated.json 기준
  const poly = item?.match?.poly;

  if (!Array.isArray(poly)) return null;
  if (!poly.every((p) => Array.isArray(p) && p.length >= 2)) return null;

  return poly.map((p) => [Number(p[0]), Number(p[1])]);
}

export default function PolygonOverlay({ items, imgSize, onSelectItem }) {
  const polygons = useMemo(() => {
    return (items || [])
      .map((item) => ({
        item,
        poly: extractPoly(item),
      }))
      .filter((x) => Array.isArray(x.poly) && x.poly.length >= 3);
  }, [items]);

  const w = imgSize?.w;
  const h = imgSize?.h;

  if (!w || !h) return null;

  return (
    <svg
      viewBox={`0 0 ${w} ${h}`}
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        pointerEvents: "none",
      }}
      preserveAspectRatio="none"
    >
      {polygons.map(({ item, poly }, idx) => {
        const points = poly.map((p) => `${p[0]},${p[1]}`).join(" ");
        return (
          <polygon
            key={idx}
            points={points}
            fill="rgba(255,0,0,0.25)"
            stroke="red"
            strokeWidth="2"
            style={{ pointerEvents: "auto", cursor: "pointer" }}
            onClick={() => onSelectItem(item)}
          />
        );
      })}
    </svg>
  );
}
