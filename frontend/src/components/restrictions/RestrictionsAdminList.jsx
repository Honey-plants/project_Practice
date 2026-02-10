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
      <div className="admin-list-panel">
        <div className="empty-list-message">
          표시할 데이터가 없습니다. (왼쪽에서 먼저 등록하세요)
        </div>
      </div>
    );
  }

  return (
    <div className="admin-list-panel">
      <h3>전체 리스트 (active 포함)</h3>

      {data.map((c) => (
        <div key={c.category_id} className="category-item-box">
          <div className="category-header">
            <strong>Category #{c.category_id}</strong>

            <input
              type="text"
              value={c.category_label_ko || ""}
              onChange={(e) => onChangeCategory(c.category_id, { category_label_ko: e.target.value })}
              placeholder="category_label_ko"
            />
            <input
              type="text"
              value={c.category_label_en || ""}
              onChange={(e) => onChangeCategory(c.category_id, { category_label_en: e.target.value })}
              placeholder="category_label_en"
            />

            <label>
              <input
                type="checkbox"
                checked={!!c.category_active}
                onChange={(e) => onChangeCategory(c.category_id, { category_active: e.target.checked })}
              />
              active
            </label>

            <button onClick={() => onSaveCategory(c)} disabled={loading} className="save-button">
              저장
            </button>
          </div>

          <div className="items-list">
            {(c.items || []).map((it) => (
              <div key={it.item_id} className="item-row">
                <span>Item #{it.item_id}</span>

                <input
                  type="text"
                  value={it.item_label_ko || ""}
                  onChange={(e) => onChangeItem(c.category_id, it.item_id, { item_label_ko: e.target.value })}
                  placeholder="item_label_ko"
                />
                <input
                  type="text"
                  value={it.item_label_en || ""}
                  onChange={(e) => onChangeItem(c.category_id, it.item_id, { item_label_en: e.target.value })}
                  placeholder="item_label_en"
                />

                <label>
                  <input
                    type="checkbox"
                    checked={!!it.item_active}
                    onChange={(e) => onChangeItem(c.category_id, it.item_id, { item_active: e.target.checked })}
                  />
                  active
                </label>

                <button onClick={() => onSaveItem(c.category_id, it)} disabled={loading} className="save-button-item">
                  저장
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
