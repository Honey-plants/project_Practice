import React from "react";
import "./MenuDetailModal.css";

export default function MenuDetailModal({ item, onClose }) {
  if (!item) return null;

  const menuNameEn = item?.menu?.menu_name_en || item?.menu_name_en || "";
  const menuDescEn = item?.menu?.menu_description_en || item?.menu_description_en || "";
  const riskDescEn = item?.risk?.risk_description_en || item?.risk_description_en || "";

  const commentKo = item?.comment?.comment_ko || item?.comment_ko || "";
  const commentEn = item?.comment?.comment_en || item?.comment_en || "";
  const hasComment = Boolean(commentKo || commentEn);

  return (
    <div className="ms-mdm__overlay" onClick={onClose}>
      <div
        className="ms-mdm__modal"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="ms-mdm__header">
          <div className="ms-mdm__titleWrap">
            <div className="ms-mdm__subtitle">Menu details (EN)</div>
            <h3 className="ms-mdm__title">
              {menuNameEn || "Menu details"}
            </h3>
          </div>

          <button className="ms-mdm__close" onClick={onClose}>
            Close
          </button>
        </div>

        {/* English description */}
        {menuDescEn && (
          <section className="ms-mdm__section">
            <h4 className="ms-mdm__sectionTitle">English description</h4>
            <p className="ms-mdm__text">{menuDescEn}</p>
          </section>
        )}

        {/* Risk */}
        {riskDescEn && (
          <section className="ms-mdm__section">
            <h4 className="ms-mdm__sectionTitle">
              Allergy / dietary risk (EN)
            </h4>
            <div className="ms-mdm__riskBox">
              <p className="ms-mdm__riskText">{riskDescEn}</p>
            </div>
          </section>
        )}

        {/* Comment for staff */}
        {hasComment && (
          <section className="ms-mdm__section">
            <div className="ms-mdm__commentHeader">
              <h4 className="ms-mdm__sectionTitle">Show this to staff</h4>
              <span className="ms-mdm__badge">show it to the staff</span>
            </div>

            <div className="ms-mdm__commentBox">
              {commentKo && (
                <div className="ms-mdm__commentBlock">
                  <div className="ms-mdm__langLabel">Korean (KO)</div>
                  <div className="ms-mdm__commentKo">{commentKo}</div>
                </div>
              )}

              {commentKo && commentEn && (
                <div className="ms-mdm__divider" />
              )}

              {commentEn && (
                <div className="ms-mdm__commentBlock">
                  <div className="ms-mdm__langLabel">English (EN)</div>
                  <div className="ms-mdm__commentEn">{commentEn}</div>
                </div>
              )}
            </div>

            <div className="ms-mdm__hint">
              Show the above sentence to the staff and check for allergy/food restriction related materials.
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
