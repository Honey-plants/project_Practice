import React, { useContext } from "react";
import { Link } from "react-router-dom";
import { MemberContext } from "../../context/MemberContext";
import styles from "./CommunityList.module.css";

export default function CommunityList({ list = [], loading = false, error = "" }) {
  const { stateMember } = useContext(MemberContext);
  const myMemberId = stateMember?.me?.member_id;
  const myNickname = stateMember?.me?.nickname;

  if (error) return <div className={styles.errorBox}>{error}</div>;
  if (loading) return <div className={styles.loading}>Loading...</div>;
  if (list.length === 0) return <div className={styles.empty}>커뮤니티 글이 없습니다.</div>;

  return (
    <div className={styles.listContainer}>
      <ul className={styles.list}>
        {list.map((row) => {
          const id = row.community_id ?? row.id;
          const imgUrl = row.image_urls?.[0] || null;
          const nickname = row.nickname || row.author_nickname || row.member_nickname
            || (row.member_id === myMemberId && myNickname ? myNickname : `익명`);

          return (
            <li key={id} className={styles.listItem}>
              <Link to={`/community/${id}`} className={styles.cardLink}>
                {/* 상단 헤더: 닉네임(왼쪽) + 좋아요(오른쪽) */}
                <div className={styles.cardHeader}>
                  <div className={styles.cardNickname}>{nickname}</div>
                  <div className={styles.cardLike}>
                    <span className={styles.likeIcon}>♥</span>
                    <span className={styles.likeCount}>{row.recommend ?? 0}</span>
                  </div>
                </div>

                {/* 이미지 영역 */}
                <div className={styles.cardImage}>
                  {imgUrl ? (
                    <img src={imgUrl} alt={`community-${id}`} className={styles.img} />
                  ) : (
                    <div className={styles.imgPlaceholder}>이미지 없음</div>
                  )}
                </div>

                {/* 최신 댓글 */}
                <div className={styles.cardComment}>
                  
                  {row.latest_comment_text
                    ? row.latest_comment_text
                    : "최신 댓글 없음"}
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}