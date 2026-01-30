import React from "react";

export default function MenuDetailModal({ item, onClose }) {
  const { menu, risk, comment } = item;

  return (
    <div className="modal-backdrop">
      <div className="modal">
        <h3>{menu?.menu_name_en}</h3>
        <p>{menu?.menu_description_en}</p>

        {risk && (
          <>
            <h4>Risk</h4>
            <p>{risk.risk_description_en}</p>
          </>
        )}

        {comment && (
          <>
            <h4>Suggested Question</h4>
            <p>{comment.comment_en}</p>
          </>
        )}

        <button onClick={onClose}>Close</button>
      </div>
    </div>
  );
}
