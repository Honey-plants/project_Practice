import React from "react";
import { Link } from "react-router-dom";
import styles from "./Section.module.css";

/**
 * CommunitySection
 * 내가 작성한 커뮤니티 글 섹션 컴포넌트
 */
export default function CommunitySection({ communities, currentPage, onPageChange }) {
  const itemsPerPage = 3;
  const totalPages = Math.ceil(communities.length / itemsPerPage);
  const communitiesToShow = communities.slice(
    currentPage * itemsPerPage,
    (currentPage + 1) * itemsPerPage
  );

  return (
    <div className={styles.section}>
      <div className={styles.header}>
        <h3 className={styles.title}>
          내가 작성한 커뮤니티 글 ({communities.length})
        </h3>
        <Link to="/community" className={styles.link}>
          전체보기 →
        </Link>
      </div>

      {communitiesToShow.length === 0 ? (
        <div className={styles.emptyState}>
          <p className={styles.emptyIcon}>💬</p>
          <p className={styles.emptyText}>작성한 커뮤니티 글이 없습니다.</p>
        </div>
      ) : (
        <>
          <div className={styles.itemList}>
            {communitiesToShow.map((community) => (
              <Link
                key={community.community_id}
                to={`/community/${community.community_id}`}
                className={`${styles.item} ${styles.communityItem}`}
              >
                <p className={styles.itemContent}>
                  {community.community_content || "내용 없음"}
                </p>
                <div className={styles.itemFooter}>
                  <span>👍 {community.recommend || 0}</span>
                  <span>
                    {new Date(community.create_at).toLocaleDateString()}
                  </span>
                </div>
              </Link>
            ))}
          </div>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              {Array.from({ length: totalPages }, (_, i) => (
                <button
                  key={i}
                  onClick={() => onPageChange(i)}
                  className={`${styles.pageButton} ${
                    currentPage === i ? styles.activeCommunity : ""
                  }`}
                >
                  {i + 1}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
