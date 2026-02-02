import React from "react";

export default function MenuDetailModal({ item, onClose }) {
  if (!item) return null;

  const menuName = item.menu_name_en || item.menu_name_ko || "Menu";
  const menuDesc = item.menu_description_en || item.menu_description_ko || "";
  const riskDesc = item.risk_description_en || item.risk_description_ko || "";
  const commentText = item.comment_en || item.comment_ko || "";

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

        {menuDesc && <p style={{ marginTop: 10, color: "#333" }}>{menuDesc}</p>}

        {riskDesc && (
          <>
            <h4 style={{ marginBottom: 6 }}>Risk</h4>
            <p style={{ marginTop: 0, color: "#b00020" }}>{riskDesc}</p>
          </>
        )}

        {commentText && (
          <>
            <h4 style={{ marginBottom: 6 }}>Suggested question for staff</h4>
            <p style={{ marginTop: 0 }}>{commentText}</p>
          </>
        )}

        <details style={{ marginTop: 12 }}>
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
