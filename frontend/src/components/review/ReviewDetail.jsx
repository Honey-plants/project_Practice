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
      console.error("카테고리 로드 실패:", e);
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
    <div className={styles.container}>
      {/* 헤더: 제목과 수정 버튼 */}
      <div className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>
            {title || "(제목 없음)"}
          </h1>
          <div className={styles.meta}>
            <span>작성일: {formatDate(createdAt)}</span>
            {location ? <span className={styles.location}>📍 {location}</span> : null}
          </div>
        </div>

        {/* 수정 버튼 */}
        {canEdit && !isUsedInContent && onEdit && isOwner && (
          <button onClick={onEdit} className={styles.editButton}>
            수정
          </button>
        )}

        {/* 컨텐츠에 사용 중일 때 수정 불가 메시지 */}
        {isUsedInContent && (
          <div className={styles.usedInContentBadge}>
            컨텐츠에 사용 중 (수정 불가)
          </div>
        )}
      </div>

      {/* 별점 */}
      <div className={styles.ratingSection}>
        <strong className={styles.ratingLabel}>별점:</strong>
        <span className={styles.stars}>{renderStars(rating)}</span>
        {rating != null ? (
          <span className={styles.ratingValue}>({rating}/5)</span>
        ) : null}
      </div>

      {/* 이미지 */}
      {images?.length > 0 && (
        <div className={styles.imagesSection}>
          <strong className={styles.sectionTitle}>
            사진
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

      {/* 카테고리 및 아이템 정보 */}
      {reviewCategories.length > 0 && (
        <div className={styles.categoriesSection}>
          <strong className={styles.sectionTitle}>
            제한 사항 / 알레르기 정보
          </strong>
          <div className={styles.categoryList}>
            {reviewCategories.map((cat) => (
              <div key={cat.category_id} className={styles.categoryCard}>
                <div className={styles.categoryLabel}>
                  {cat.category_label_ko || cat.category_label_en || `Category #${cat.category_id}`}
                </div>
                <div className={styles.itemTags}>
                  {cat.matchedItems.map((item) => (
                    <span key={item.item_id} className={styles.itemTag}>
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
      {menuName && (
        <div className={styles.menuSection}>
          <strong className={styles.sectionTitle}>
            영수증 메뉴
          </strong>
          <div className={styles.menuTags}>
            {(Array.isArray(menuName)
              ? menuName
              : menuName.split(',')
            ).map((m, idx) => (
              <span key={`${m}-${idx}`} className={styles.menuTag}>
                🍽️ {String(m).replace(/["[\]]/g, '').trim()}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 리뷰 내용 */}
      <div className={styles.contentSection}>
        <strong className={styles.sectionTitle}>
          리뷰 내용
        </strong>
        <div className={styles.contentBox}>
          {content || "-"}
        </div>
      </div>
    </div>
  );
}
