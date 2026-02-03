import React from "react";

export default function MenuDetailModal({ item, onClose }) {
  if (!item) return null;

  // Step06(final_translated.json) 기준 구조 방어
  // - item.menu.menu_name_en, item.menu.menu_description_en
  // - item.risk.risk_description_en
  // - item.comment.comment_en
  const menuName =
    item?.menu?.menu_name_en ||
    item?.menu?.menu_name_ko ||
    item?.menu_name_en ||
    item?.menu_name_ko ||
    "Menu";

  const menuDesc =
    item?.menu?.menu_description_en ||
    item?.menu?.menu_description_ko ||
    item?.menu_description_en ||
    item?.menu_description_ko ||
    "";

  const riskDesc =
    item?.risk?.risk_description_en ||
    item?.risk?.risk_description_ko ||
    item?.risk_description_en ||
    item?.risk_description_ko ||
    "";

  const commentText =
    item?.comment?.comment_en ||
    item?.comment?.comment_ko ||
    item?.comment_en ||
    item?.comment_ko ||
    "";

  const algTags =
    item?.menu?.alg_tags ||
    item?.alg_tags ||
    item?.risk?.alg_tags ||
    item?.risk?.matched_allergens ||
    [];

  const copy = async (text) => {
    try {
      await navigator.clipboard.writeText(String(text || ""));
    } catch (_) {
      // clipboard 권한이 없을 수 있어 조용히 무시
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
        zIndex: 9999,
      }}
      onClick={onClose}
    >
      <div
        style={{
          width: "min(720px, 100%)",
          background: "#fff",
          borderRadius: 12,
          padding: 16,
          boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
          <h3 style={{ margin: 0 }}>{menuName}</h3>
          <button onClick={onClose}>Close</button>
        </div>

        {Array.isArray(algTags) && algTags.length > 0 && (
          <div style={{ marginTop: 10, fontSize: 13, color: "#444" }}>
            <b>Allergen tags:</b> {algTags.join(", ")}
          </div>
        )}

        {menuDesc && (
          <div style={{ marginTop: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <h4 style={{ margin: 0 }}>English description</h4>
              <button onClick={() => copy(menuDesc)} style={{ fontSize: 12 }}>
                Copy
              </button>
            </div>
            <p style={{ marginTop: 8, color: "#333" }}>{menuDesc}</p>
          </div>
        )}

        {riskDesc && (
          <div style={{ marginTop: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <h4 style={{ margin: 0 }}>Allergy / dietary risk (EN)</h4>
              <button onClick={() => copy(riskDesc)} style={{ fontSize: 12 }}>
                Copy
              </button>
            </div>
            <p style={{ marginTop: 8, color: "#b00020" }}>{riskDesc}</p>
          </div>
        )}

        {commentText && (
          <div style={{ marginTop: 12 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <h4 style={{ margin: 0 }}>Comment / question for staff (EN)</h4>
              <button onClick={() => copy(commentText)} style={{ fontSize: 12 }}>
                Copy
              </button>
            </div>
            <p style={{ marginTop: 8 }}>{commentText}</p>
          </div>
        )}

        <details style={{ marginTop: 14 }}>
          <summary style={{ cursor: "pointer" }}>item JSON 보기</summary>
          <pre
            style={{
              whiteSpace: "pre-wrap",
              background: "#f6f8fa",
              padding: 10,
              borderRadius: 8,
            }}
          >
            {JSON.stringify(item, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  );
}
