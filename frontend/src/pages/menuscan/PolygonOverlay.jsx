import React, { useMemo } from "react";

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

/**
 * SVG 텍스트 폭을 “추정”해서 폰트 크기를 잡는다.
 * (getComputedTextLength 같은 DOM 측정 없이도 안정적으로 동작)
 */
function estimateTextWidthPx(text, fontSize) {
  const s = String(text || "");
  const base = 0.56; // 대략적인 글자폭 계수 (영문 기준)
  let units = 0;

  for (const ch of s) {
    if (ch === " " || ch === "-") units += 0.30;
    else if (ch === ".") units += 0.22;
    else units += 1.0;
  }

  return units * base * fontSize;
}

/**
 * 가능하면 2줄로 래핑 (공백 기준).
 * 공백이 없으면 1줄 고정 (폰트만 축소).
 */
function wrapToTwoLines(text) {
  const s = String(text || "").trim();
  if (!s) return [];

  const parts = s.split(/\s+/);
  if (parts.length <= 1) return [s];

  // 반으로 나누되 자연스러운 분할(대충 중앙)
  const mid = Math.ceil(parts.length / 2);
  const l1 = parts.slice(0, mid).join(" ");
  const l2 = parts.slice(mid).join(" ");
  return l2 ? [l1, l2] : [l1];
}

/**
 * 박스 크기에 맞는 폰트 크기 선택
 * - 2줄이면 높이 제한도 고려
 * - padding 고려
 */
function pickFontSizeForBox(lines, boxW, boxH, maxFont = 22, minFont = 10) {
  if (!lines || lines.length === 0) return minFont;

  // padding (박스가 작을수록 최소 padding 유지)
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
        const bbox = getBBox(poly);
        const label = getLabel(item);

        // 기본: 2줄 래핑 시도
        let lines = wrapToTwoLines(label);

        // 박스 높이가 너무 낮으면 1줄로 강제 (2줄이면 잘릴 수 있음)
        if (bbox.h < 32 && label) lines = [label];

        // 폰트 크기 자동 선택
        const fs = pickFontSizeForBox(lines, bbox.w, bbox.h, 22, 10);

        // 중앙 위치
        const [cx, cy] = centroid(poly);

        // 줄 시작 y 계산 (중앙 정렬)
        const lineH = fs * 1.1;
        const startY = lines.length <= 1 ? cy : cy - (lineH * (lines.length - 1)) / 2;

        return (
          <g
            key={idx}
            style={{ pointerEvents: "auto", cursor: "pointer" }}
            onClick={() => onSelectItem?.(item)}
          >
            <polygon
              points={points}
              fill="rgba(255, 0, 0, 0.20)"
              stroke="red"
              strokeWidth="2"
            />

            {lines.length > 0 && (
              <text
                x={cx}
                y={startY}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize={fs}
                fontWeight="700"
                // 흰 테두리로 가독성 확보
                stroke="white"
                strokeWidth={Math.max(2, fs * 0.12)}
                paintOrder="stroke"
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
