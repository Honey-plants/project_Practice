import React, { useMemo } from "react";

/**
 * RestrictionsPicker
 *
 * props:
 * - categories: [{category_id, category_label_ko/en, category_active, items:[{item_id, item_label_ko/en, item_active}]}]
 * - selectedIds: number[]
 * - onToggle: (itemId:number)=>void   // 있으면 checkbox 모드
 * - mode: "select" | "view"           // select: 체크박스 / view: 선택된 것만 표시(읽기)
 * - onlyActive: boolean               // true면 active만 필터
 */
export default function RestrictionsPicker({
  categories = [],
  selectedIds = [],
  onToggle,
  mode = "select",
  onlyActive = true,
}) {
  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);

  const filtered = useMemo(() => {
    const catList = Array.isArray(categories) ? categories : [];

    return catList
      .filter((c) => (onlyActive ? c.category_active !== false : true))
      .map((c) => {
        const items = (c.items || [])
          .filter((it) => (onlyActive ? it.item_active !== false : true))
          // view 모드면 선택된 것만 보여줌
          .filter((it) => (mode === "view" ? selectedSet.has(it.item_id) : true));

        return { ...c, items };
      })
      .filter((c) => (c.items || []).length > 0);
  }, [categories, onlyActive, mode, selectedSet]);

  if (filtered.length === 0) {
    return (
      <div style={{ padding: 12, border: "1px solid #ddd", borderRadius: 6 }}>
        표시할 항목이 없습니다.
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {filtered.map((c) => (
        <div key={c.category_id} className="card" style={{ padding: 12 }}>
          <div style={{ fontWeight: 700, marginBottom: 10 }}>
            {c.category_label_ko ?? c.category_label_en ?? `Category#${c.category_id}`}
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {(c.items || []).map((it) => {
              const id = it.item_id;
              const label = it.item_label_ko ?? it.item_label_en ?? `item#${id}`;
              const checked = selectedSet.has(id);

              // view 모드(읽기 전용): 뱃지 형태
              if (mode === "view") {
                return (
                  <span
                    key={id}
                    style={{
                      padding: "6px 10px",
                      border: "1px solid #ddd",
                      borderRadius: 999,
                      background: "#e6ffed",
                      fontWeight: 700,
                    }}
                  >
                    {label}
                  </span>
                );
              }

              // select 모드: checkbox
              return (
                <label
                  key={id}
                  style={{
                    display: "inline-flex",
                    gap: 8,
                    alignItems: "center",
                    border: "1px solid #ddd",
                    borderRadius: 999,
                    padding: "6px 10px",
                    cursor: "pointer",
                    userSelect: "none",
                    background: checked ? "#e6ffed" : "transparent",
                    fontWeight: checked ? 700 : 400,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => onToggle?.(id)}
                    style={{ margin: 0 }}
                  />
                  <span>{label}</span>
                </label>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}