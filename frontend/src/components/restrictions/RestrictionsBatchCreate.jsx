import React, { useState } from "react";
import { RestrictionsAdminAPI } from "../../api/restrictionsAdminApi";

export default function RestrictionsBatchCreate({ onSaved }) {
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const [draft, setDraft] = useState([
    { category_label_ko: "", category_label_en: "", items: [] },
  ]);

  const addCategory = () => {
    setDraft((p) => [...p, { category_label_ko: "", category_label_en: "", items: [] }]);
  };

  const removeCategory = (cIdx) => {
    setDraft((p) => p.filter((_, i) => i !== cIdx));
  };

  const updateCategory = (idx, patch) => {
    setDraft((p) => p.map((c, i) => (i === idx ? { ...c, ...patch } : c)));
  };

  const addItem = (cIdx) => {
    setDraft((p) =>
      p.map((c, i) => (i === cIdx ? { ...c, items: [...(c.items || []), { item_label_ko: "", item_label_en: "" }] } : c))
    );
  };

  const removeItem = (cIdx, itIdx) => {
    setDraft((p) =>
      p.map((c, i) => {
        if (i !== cIdx) return c;
        return { ...c, items: (c.items || []).filter((_, j) => j !== itIdx) };
      })
    );
  };

  const updateItem = (cIdx, itIdx, patch) => {
    setDraft((p) =>
      p.map((c, i) => {
        if (i !== cIdx) return c;
        return { ...c, items: (c.items || []).map((it, j) => (j === itIdx ? { ...it, ...patch } : it)) };
      })
    );
  };

  const buildPayload = () => {
    const categories = draft
      .map((c) => ({
        category_label_ko: (c.category_label_ko || "").trim(),
        category_label_en: (c.category_label_en || "").trim(),
        items: (c.items || [])
          .map((it) => ({
            item_label_ko: (it.item_label_ko || "").trim(),
            item_label_en: (it.item_label_en || "").trim(),
          }))
          .filter((it) => it.item_label_ko || it.item_label_en),
      }))
      .filter((c) => c.category_label_ko || c.category_label_en);

    return { categories };
  };

  const submit = async () => {
    setMsg("");
    setSaving(true);
    try {
      const payload = buildPayload();
      if (!payload.categories.length) {
        setMsg("❌ 등록할 카테고리가 없습니다 (label_ko/en 중 하나는 입력)");
        return;
      }

      await RestrictionsAdminAPI.batchCreate(payload);
      setMsg(" 일괄 등록 완료");
      setDraft([{ category_label_ko: "", category_label_en: "", items: [] }]);
      onSaved && (await onSaved());
    } catch (e) {
      const detail = e?.response?.data?.detail || e?.message || "배치 등록 실패";
      setMsg(`❌ ${typeof detail === "string" ? detail : JSON.stringify(detail)}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="batch-create-panel">
      <h3>기본 등록 (Batch)</h3>

      {draft.map((c, cIdx) => (
        <div key={cIdx} className="batch-category-box">
          <div className="batch-category-header">
            <div className="batch-category-inputs">
              <input
                value={c.category_label_ko}
                onChange={(e) => updateCategory(cIdx, { category_label_ko: e.target.value })}
                placeholder="category_label_ko"
              />
              <input
                value={c.category_label_en}
                onChange={(e) => updateCategory(cIdx, { category_label_en: e.target.value })}
                placeholder="category_label_en"
              />
              <button onClick={() => addItem(cIdx)} className="add-item-button">+ item</button>
              {draft.length > 1 && (
                <button onClick={() => removeCategory(cIdx)} className="remove-category-button">
                  × 카테고리 삭제
                </button>
              )}
            </div>
          </div>

          {(c.items || []).length > 0 && (
            <div className="batch-items-list">
              {(c.items || []).map((it, itIdx) => (
                <div key={itIdx} className="batch-item-row">
                  <input
                    value={it.item_label_ko}
                    onChange={(e) => updateItem(cIdx, itIdx, { item_label_ko: e.target.value })}
                    placeholder="item_label_ko"
                  />
                  <input
                    value={it.item_label_en}
                    onChange={(e) => updateItem(cIdx, itIdx, { item_label_en: e.target.value })}
                    placeholder="item_label_en"
                  />
                  <button onClick={() => removeItem(cIdx, itIdx)} className="remove-item-button">
                    × 삭제
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}

      <div className="batch-actions">
        <button onClick={addCategory}>+ category</button>
        <button onClick={submit} disabled={saving}>
          {saving ? "저장중..." : "일괄 등록"}
        </button>
      </div>

      {msg && <div className="batch-message">{msg}</div>}
    </div>
  );
}
