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
          A Written Review ({reviews.length})
        </h3>
        <Link to="/review" className={styles.link}>
          All review
        </Link>
      </div>

      {reviewsToShow.length === 0 ? (
        <div className={styles.emptyState}>
          <p className={styles.emptyIcon}>📝</p>
          <p className={styles.emptyText}>No reviews have been created.</p>
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
                  {review.review_title || "Untitled"}
                </h4>
                <p className={styles.itemContent}>
                  {review.review_content || "No content"}
                </p>
                <div className={styles.itemFooter}>
                  <span>⭐ {review.rating || 0}</span>
                </div>
              </Link>
            ))}
          </div>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button
                onClick={() => onPageChange(Math.max(0, currentPage - 1))}
                disabled={currentPage === 0}
                className={`${styles.pageButton} ${currentPage === 0 ? styles.disabled : ''}`}
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
                className={`${styles.pageButton} ${currentPage === totalPages - 1 ? styles.disabled : ''}`}
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
