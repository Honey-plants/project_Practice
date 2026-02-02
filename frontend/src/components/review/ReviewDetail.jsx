import { useState, useEffect } from "react";
import { MetaAPI } from "../../api/metaApi";

function formatDate(v) {
  if (!v) return "-";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return String(v);
  return d.toLocaleString();
}

function renderStars(rating) {
  const n = Number(rating);
  if (!Number.isFinite(n)) return "-";
  const clamped = Math.max(0, Math.min(5, Math.round(n)));
  return "★".repeat(clamped) + "☆".repeat(5 - clamped);
}

export function ReviewDetail({ review, onEdit, canEdit = true, isUsedInContent = false }) {
  const [categories, setCategories] = useState([]);

  console.log("review :: ", review)

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await MetaAPI.getActiveRestrictions();
      // 응답 형식: { etag: "...", data: [...] }
      const list = response.data?.data || response.data || [];
      setCategories(list);
    } catch (e) {
      console.error("카테고리 로드 실패:", e);
    }
  };

  if (!review) return null;

  const { title, content, rating, createdAt, images, menuNames, location, itemIds, menuName } = review;

  // review_items를 배열로 변환
  const reviewItemIds = (() => {
    if (!itemIds || itemIds.length === 0) return [];
    if (Array.isArray(itemIds)) return itemIds.map(id => Number(id));
    if (typeof itemIds === 'string') {
      return itemIds.split(',').map(id => Number(id.trim()));
    }
    return [];
  })();

  // 리뷰에 포함된 카테고리 및 아이템 정보 추출
  const reviewCategories = categories
    .map(cat => {
      const matchedItems = (cat.items || []).filter(item =>
        reviewItemIds.includes(item.item_id)
      );
      if (matchedItems.length > 0) {
        return { ...cat, matchedItems };
      }
      return null;
    })
    .filter(Boolean);

  return (
    <div
      style={{
        border: "1px solid #eee",
        borderRadius: 12,
        padding: 24,
        display: "grid",
        gap: 20,
        background: "white"
      }}
    >
      {/* 헤더: 제목과 수정 버튼 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div style={{ flex: 1 }}>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: "#212529" }}>
            {title || "(제목 없음)"}
          </h1>
          <div style={{ marginTop: 8, fontSize: 14, color: "#6c757d" }}>
            <span>작성일: {formatDate(createdAt)}</span>
            {location ? <span style={{ marginLeft: 16 }}>📍 {location}</span> : null}
          </div>
        </div>

        {/* 수정 버튼 */}
        {canEdit && !isUsedInContent && onEdit && (
          <button
            onClick={onEdit}
            style={{
              padding: "8px 16px",
              background: "#007bff",
              color: "white",
              border: "none",
              borderRadius: "6px",
              cursor: "pointer",
              fontSize: "14px",
              fontWeight: "600"
            }}
          >
            수정
          </button>
        )}

        {/* 컨텐츠에 사용 중일 때 수정 불가 메시지 */}
        {isUsedInContent && (
          <div style={{
            padding: "8px 16px",
            background: "#ffc107",
            color: "#856404",
            border: "1px solid #ffc107",
            borderRadius: "6px",
            fontSize: "13px",
            fontWeight: "600"
          }}>
            컨텐츠에 사용 중 (수정 불가)
          </div>
        )}
      </div>

      {/* 별점 */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <strong style={{ fontSize: 15, color: "#495057" }}>별점:</strong>
        <span style={{ fontSize: 20, color: "#ffc107" }}>{renderStars(rating)}</span>
        {rating != null ? (
          <span style={{ fontSize: 14, color: "#6c757d" }}>({rating}/5)</span>
        ) : null}
      </div>

      {/* 이미지 */}
      {images?.length > 0 && (
        <div>
          <strong style={{ fontSize: 15, color: "#495057", display: "block", marginBottom: 12 }}>
            사진
          </strong>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: images.length === 1 ? "1fr" : images.length === 2 ? "repeat(2, 1fr)" : "repeat(3, 1fr)",
              gap: 12,
            }}
          >
            {images.slice(0, 3).map((src, idx) => (
              <div
                key={`${src}-${idx}`}
                style={{
                  border: "1px solid #e0e0e0",
                  borderRadius: 12,
                  overflow: "hidden",
                  aspectRatio: "1 / 1",
                  background: "#f8f9fa",
                }}
              >
                <img
                  src={src}
                  alt={`review-${idx}`}
                  style={{ width: "100%", height: "100%", objectFit: "cover" }}
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 카테고리 및 아이템 정보 */}
      {reviewCategories.length > 0 && (
        <div>
          <strong style={{ fontSize: 15, color: "#495057", display: "block", marginBottom: 12 }}>
            제한 사항 / 알레르기 정보
          </strong>
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            {reviewCategories.map((cat) => (
              <div
                key={cat.category_id}
                style={{
                  padding: "12px",
                  background: "#f8f9fa",
                  borderRadius: "8px",
                  border: "1px solid #e0e0e0"
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 8, color: "#495057", fontSize: 14 }}>
                  {cat.category_label_ko || cat.category_label_en || `Category #${cat.category_id}`}
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {cat.matchedItems.map((item) => (
                    <span
                      key={item.item_id}
                      style={{
                        padding: "6px 12px",
                        background: "#fff3cd",
                        color: "#856404",
                        borderRadius: 16,
                        fontSize: 13,
                        fontWeight: 500,
                        border: "1px solid #ffeaa7"
                      }}
                    >
                      {item.item_label_ko || item.item_label_en || `Item #${item.item_id}`}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 메뉴명(영수증 디텍트 결과) */}
      {menuName?.length > 0 && (
        <div>
          <strong style={{ fontSize: 15, color: "#495057", display: "block", marginBottom: 12 }}>
            영수증 메뉴
          </strong>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {menuName.map((m, idx) => (
              <span
                key={`${m}-${idx}`}
                style={{
                  padding: "6px 12px",
                  border: "1px solid #dee2e6",
                  borderRadius: 16,
                  fontSize: 13,
                  background: "#e9ecef",
                  color: "#495057"
                }}
              >
                {m}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 리뷰 내용 */}
      <div>
        <strong style={{ fontSize: 15, color: "#495057", display: "block", marginBottom: 12 }}>
          리뷰 내용
        </strong>
        <div
          style={{
            marginTop: 8,
            whiteSpace: "pre-wrap",
            lineHeight: 1.7,
            fontSize: 15,
            color: "#212529",
            padding: "16px",
            background: "#f8f9fa",
            borderRadius: "8px",
            border: "1px solid #e0e0e0"
          }}
        >
          {content || "-"}
        </div>
      </div>
    </div>
  );
}
