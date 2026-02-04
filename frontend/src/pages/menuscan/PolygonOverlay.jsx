import React, { useMemo } from "react";
import "./PolygonOverlay.css";

/**
 * [확정된 최신 구조]
 * - poly: item.match.poly
 * - label: item.menu.menu_name_en (fallback: ko)
 *
 * 목표:
 * - poly 박스 표시
 * - 박스 크기에 맞춰 글씨(영문 메뉴명) 자동 크기 조절
 * - 길면 2줄까지 자동 래핑(tspan)
 * - 클릭 시 onSelectItem(item)
 */

function extractPoly(item) {
  const poly = item?.match?.poly;

  if (!Array.isArray(poly)) return null;
  if (!poly.every((p) => Array.isArray(p) && p.length >= 2)) return null;

  return poly
    .map((p) => [Number(p[0]), Number(p[1])])
    .filter((p) => Number.isFinite(p[0]) && Number.isFinite(p[1]));
}

function getLabel(item) {
  return item?.menu?.menu_name_en || item?.menu?.menu_name_ko || "";
}

function centroid(poly) {
  const n = poly.length;
  const sx = poly.reduce((a, p) => a + p[0], 0);
  const sy = poly.reduce((a, p) => a + p[1], 0);
  return [sx / n, sy / n];
}

function getBBox(poly) {
  let minX = Infinity,
    minY = Infinity,
    maxX = -Infinity,
    maxY = -Infinity;

  for (const [x, y] of poly) {
    if (x < minX) minX = x;
    if (y < minY) minY = y;
    if (x > maxX) maxX = x;
    if (y > maxY) maxY = y;
  }

  return { minX, minY, maxX, maxY, w: maxX - minX, h: maxY - minY };
}

function estimateTextWidthPx(text, fontSize) {
  const s = String(text || "");
  const base = 0.56;
  let units = 0;

  for (const ch of s) {
    if (ch === " " || ch === "-") units += 0.30;
    else if (ch === ".") units += 0.22;
    else units += 1.0;
  }

  return units * base * fontSize;
}

function wrapToTwoLines(text) {
  const s = String(text || "").trim();
  if (!s) return [];

  const parts = s.split(/\s+/);
  if (parts.length <= 1) return [s];

  const mid = Math.ceil(parts.length / 2);
  const l1 = parts.slice(0, mid).join(" ");
  const l2 = parts.slice(mid).join(" ");
  return l2 ? [l1, l2] : [l1];
}

function pickFontSizeForBox(lines, boxW, boxH, maxFont = 22, minFont = 10) {
  if (!lines || lines.length === 0) return minFont;

  const padX = Math.max(6, boxW * 0.06);
  const padY = Math.max(4, boxH * 0.10);
  const availW = Math.max(0, boxW - padX * 2);
  const availH = Math.max(0, boxH - padY * 2);

  const lineCount = lines.length;

  for (let fs = maxFont; fs >= minFont; fs -= 1) {
    const lineH = fs * 1.1;
    const totalH = lineH * lineCount;
    if (totalH > availH) continue;

    const widest = Math.max(...lines.map((t) => estimateTextWidthPx(t, fs)));
    if (widest <= availW) return fs;
  }

  return minFont;
}

export default function PolygonOverlay({ items, imgSize, onSelectItem }) {
  const polygons = useMemo(() => {
    if (!Array.isArray(items)) return [];
    return items
      .map((item) => ({ item, poly: extractPoly(item) }))
      .filter((x) => Array.isArray(x.poly) && x.poly.length >= 3);
  }, [items]);

  const w = imgSize?.w || 0;
  const h = imgSize?.h || 0;
  if (!w || !h || polygons.length === 0) return null;

  return (
    <svg className="ms-po__svg" viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
      {polygons.map(({ item, poly }, idx) => {
        const points = poly.map((p) => `${p[0]},${p[1]}`).join(" ");
        const bbox = getBBox(poly);
        const label = getLabel(item);

        let lines = wrapToTwoLines(label);
        if (bbox.h < 32 && label) lines = [label];

        const fs = pickFontSizeForBox(lines, bbox.w, bbox.h, 22, 10);

        const [cx, cy] = centroid(poly);

        const lineH = fs * 1.1;
        const startY = lines.length <= 1 ? cy : cy - (lineH * (lines.length - 1)) / 2;
        const color = item?.ui?.color || (["exact","close"].includes((item?.match?.status || "").toLowerCase()) ? "red" : "orange");

        return (
          <g key={idx} className="ms-po__group" onClick={() => onSelectItem?.(item)}>
            <polygon className={`ms-po__poly ms-po__poly--${color}`} points={points} />

            {lines.length > 0 && (
              <text
                className="ms-po__text"
                x={cx}
                y={startY}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={fs}
                strokeWidth={Math.max(2, fs * 0.12)}
              >
                {lines.map((t, i) => (
                  <tspan key={i} x={cx} y={startY + i * lineH}>
                    {t}
                  </tspan>
                ))}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}
