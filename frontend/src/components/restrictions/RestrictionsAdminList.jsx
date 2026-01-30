import React from "react";

export default function RestrictionsAdminList({
  data = [],
  loading = false,
  onChangeCategory,
  onChangeItem,
  onSaveCategory,
  onSaveItem,
}) {
  if (!data.length) {
    return (
      <div style={{ padding: 12, border: "1px solid #ddd" }}>
        표시할 데이터가 없습니다. (왼쪽에서 먼저 등록하세요)
      </div>
    );
  }

  return (
    <div style={{ padding: 12, border: "1px solid #ddd" }}>
      <h3 style={{ marginTop: 0 }}>전체 리스트 (active 포함)</h3>

      {data.map((c) => (
        <div key={c.category_id} style={{ border: "1px solid #eee", padding: 12, marginBottom: 12 }}>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
            <strong>Category #{c.category_id}</strong>

            <input
              value={c.category_label_ko || ""}
              onChange={(e) => onChangeCategory(c.category_id, { category_label_ko: e.target.value })}
              placeholder="category_label_ko"
            />
            <input
              value={c.category_label_en || ""}
              onChange={(e) => onChangeCategory(c.category_id, { category_label_en: e.target.value })}
              placeholder="category_label_en"
            />

            <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
              <input
                type="checkbox"
                checked={!!c.category_active}
                onChange={(e) => onChangeCategory(c.category_id, { category_active: e.target.checked })}
              />
              active
            </label>

            <button onClick={() => onSaveCategory(c)} disabled={loading}>저장</button>
          </div>

          <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 8 }}>
            {(c.items || []).map((it) => (
              <div key={it.item_id} style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                <span style={{ minWidth: 80 }}>Item #{it.item_id}</span>

                <input
                  value={it.item_label_ko || ""}
                  onChange={(e) => onChangeItem(c.category_id, it.item_id, { item_label_ko: e.target.value })}
                  placeholder="item_label_ko"
                />
                <input
                  value={it.item_label_en || ""}
                  onChange={(e) => onChangeItem(c.category_id, it.item_id, { item_label_en: e.target.value })}
                  placeholder="item_label_en"
                />

                <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <input
                    type="checkbox"
                    checked={!!it.item_active}
                    onChange={(e) => onChangeItem(c.category_id, it.item_id, { item_active: e.target.checked })}
                  />
                  active
                </label>

                <button onClick={() => onSaveItem(c.category_id, it)} disabled={loading}>저장</button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
