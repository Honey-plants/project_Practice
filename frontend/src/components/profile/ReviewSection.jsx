import React from "react";
import { Link } from "react-router-dom";
import styles from "./Section.module.css";

/**
 * ReviewSection
 * 내가 작성한 리뷰 섹션 컴포넌트
 */
export default function ReviewSection({ reviews, currentPage, onPageChange }) {
  const itemsPerPage = 3;
  const totalPages = Math.ceil(reviews.length / itemsPerPage);
  const reviewsToShow = reviews.slice(
    currentPage * itemsPerPage,
    (currentPage + 1) * itemsPerPage
  );

  return (
    <div className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>
          내가 작성한 리뷰 ({reviews.length})
        </h3>
        <Link to="/review" className={styles.link}>
          전체보기 →
        </Link>
      </div>

      {reviewsToShow.length === 0 ? (
        <div className={styles.emptyState}>
          <p className={styles.emptyIcon}>📝</p>
          <p className={styles.emptyText}>작성한 리뷰가 없습니다.</p>
        </div>
      ) : (
        <>
          <div className={styles.itemList}>
            {reviewsToShow.map((review) => (
              <Link
                key={review.review_id}
                to={`/review/${review.review_id}`}
                className={styles.item}
              >
                <h4 className={styles.itemTitle}>
                  {review.review_title || "제목 없음"}
                </h4>
                <p className={styles.itemContent}>
                  {review.review_content || "내용 없음"}
                </p>
                <div className={styles.itemFooter}>
                  <span>⭐ {review.rating || 0}</span>
                  <span>{review.location || "위치 미상"}</span>
                </div>
              </Link>
            ))}
          </div>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button
                onClick={() => onPageChange(Math.max(0, currentPage - 1))}
                disabled={currentPage === 0}
                className={styles.pageButton}
                style={{
                  opacity: currentPage === 0 ? 0.3 : 1,
                  cursor: currentPage === 0 ? "not-allowed" : "pointer"
                }}
              >
                &lt;
              </button>

              {Array.from({ length: totalPages }, (_, i) => (
                <button
                  key={i}
                  onClick={() => onPageChange(i)}
                  className={`${styles.pageButton} ${
                    currentPage === i ? styles.active : ""
                  }`}
                >
                  {i + 1}
                </button>
              ))}

              <button
                onClick={() => onPageChange(Math.min(totalPages - 1, currentPage + 1))}
                disabled={currentPage === totalPages - 1}
                className={styles.pageButton}
                style={{
                  opacity: currentPage === totalPages - 1 ? 0.3 : 1,
                  cursor: currentPage === totalPages - 1 ? "not-allowed" : "pointer"
                }}
              >
                &gt;
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
