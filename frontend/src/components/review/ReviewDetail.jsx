import { useState, useEffect } from "react";
import { MetaAPI } from "../../api/metaApi";
import styles from "./ReviewDetail.module.css";

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

export function ReviewDetail({ review, onEdit, canEdit = true, isUsedInContent = false, currentMemberId = null }) {
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
      console.error("Failed to load category:", e);
    }
  };

  if (!review) return null;

  const { title, content, rating, createdAt, images, location, itemIds, menuName } = review;

  // 현재 로그인한 사용자와 리뷰 작성자가 일치하는지 확인
  // 타입을 숫자로 통일해서 비교 (백엔드에서 숫자로 오지만 혹시 모를 타입 불일치 방지)
  const reviewMemberId = Number(review.raw?.member_id);
  const loginMemberId = Number(currentMemberId);
  const isOwner = loginMemberId > 0 && reviewMemberId > 0 && loginMemberId === reviewMemberId;

  console.log("=== Owner Check Debug ===");
  console.log("currentMemberId:", currentMemberId, typeof currentMemberId);
  console.log("review.raw?.member_id:", review.raw?.member_id, typeof review.raw?.member_id);
  console.log("isOwner:", isOwner);


  // review_items를 배열로 변환
  const reviewItemIds = (() => {
    if (!itemIds || itemIds.length === 0) return [];
    if (Array.isArray(itemIds)) return itemIds.map(id => Number(id));
    if (typeof itemIds === 'string') {
      return itemIds.split(',').map(id => Number(id.trim()));
    }
    return [];
  })();

  // 리뷰에 포함된 아이템 정보만 추출 (카테고리 제외)
  const reviewItems = [];
  categories.forEach(cat => {
    (cat.items || []).forEach(item => {
      if (reviewItemIds.includes(item.item_id)) {
        reviewItems.push({
          id: item.item_id,
          label: item.item_label_en || item.item_label_ko || `Item #${item.item_id}`
        });
      }
    });
  });

  return (
    <div className={styles.container}>
      {/* 헤더: 제목과 수정 버튼 */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>
            {title || "(No title)"}
          </h1>
          <div className={styles.meta}>
            <span>Date of creation: {formatDate(createdAt)}</span>
            {location ? <span className={styles.location}>📍 {location}</span> : null}
          </div>
        </div>

        {/* 수정 버튼 */}
        {canEdit && !isUsedInContent && onEdit && isOwner && (
          <button onClick={onEdit} className={styles.editButton}>
            Edit
          </button>
        )}

        {/* 컨텐츠에 사용 중일 때 수정 불가 메시지 */}
        {isUsedInContent && (
          <div className={styles.usedInContentBadge}>
            In use with content (non-modifiable)
          </div>
        )}
      </div>

      {/* 별점 */}
      <div className={styles.ratingSection}>
        <strong className={styles.ratingLabel}>Rating:</strong>
        <span className={styles.stars}>{renderStars(rating)}</span>
        {rating != null ? (
          <span className={styles.ratingValue}>({rating}/5)</span>
        ) : null}
      </div>

      {/* 이미지 */}
      {images?.length > 0 && (
        <div className={styles.imagesSection}>
          <strong className={styles.sectionTitle}>
          </strong>
          <div
            className={`${styles.imageGrid} ${
              images.length === 1 ? styles.single :
              images.length === 2 ? styles.double :
              styles.triple
            }`}
          >
            {images.slice(0, 3).map((src, idx) => (
              <div key={`${src}-${idx}`} className={styles.imageWrapper}>
                <img
                  src={src}
                  alt={`review-${idx}`}
                  className={styles.image}
                  onError={(e) => {
                    e.currentTarget.style.display = "none";
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 아이템 정보 (카테고리 없이 아이템만 표시) */}
      {reviewItems.length > 0 && (
        <div className={styles.itemsSection}>
          <strong className={styles.sectionTitle}>
            Restrictions / Allergy Information
          </strong>
          <div className={styles.itemTags}>
            {reviewItems.map((item) => (
              <span key={item.id} className={styles.itemTag}>
                {item.label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 메뉴명(영수증 디텍트 결과) */}
      {menuName && (
        <div className={styles.menuSection}>
          <strong className={styles.sectionTitle}>
            Menu
          </strong>
          <div className={styles.menuTags}>
            {(Array.isArray(menuName)
              ? menuName
              : menuName.split(',')
            ).map((m, idx) => (
              <span key={`${m}-${idx}`} className={styles.menuTag}>
                {String(m).replace(/["[\]]/g, '').trim()}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 리뷰 내용 */}
      <div className={styles.contentSection}>
        <strong className={styles.sectionTitle}>
          Content
        </strong>
        <div className={styles.contentBox}>
          {content || "-"}
        </div>
      </div>
    </div>
  );
}
