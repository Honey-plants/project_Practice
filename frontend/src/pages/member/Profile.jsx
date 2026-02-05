import React, { useContext, useEffect, useState, useMemo } from "react";
import { MemberContext } from "../../context/MemberContext";
import { ReviewContext } from "../../context/ReviewContext";
import { CommunityContext } from "../../context/CommunityContext";
import ProfileSidebar from "../../components/profile/ProfileSidebar";
import RestrictionsSection from "../../components/profile/RestrictionsSection";
import ReviewSection from "../../components/profile/ReviewSection";
import CommunitySection from "../../components/profile/CommunitySection";
import styles from "./Profile.module.css";

/**
 * Profile
 * 1) 본인 정보 노출 (왼쪽 사이드바)
 * 2) 본인이 선택한 item_ids만 "읽기 전용"으로 표시
 * 3) 내가 작성한 리뷰 목록
 * 4) 내가 작성한 커뮤니티 글 목록
 */
export default function Profile() {
  const { stateMember, memberActions } = useContext(MemberContext);
  const { stateReview, reviewActions } = useContext(ReviewContext);
  const { stateCommunity, communityActions } = useContext(CommunityContext);

  const [reviewPage, setReviewPage] = useState(0);
  const [communityPage, setCommunityPage] = useState(0);

  const me = stateMember.me;

  // 내가 선택한 item_ids
  const selectedIds = useMemo(() => (me?.item_ids ? me.item_ids : []), [me]);

  // 새로고침 직후 me가 없으면 로드
  useEffect(() => {
    if (!me && !stateMember?.loading) {
      memberActions?.loadMe?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 리뷰와 커뮤니티 데이터 로드
  useEffect(() => {
    reviewActions.fetchMyList();
    communityActions.fetchMyList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 내가 작성한 리뷰만 필터링
  const myReviews = useMemo(() => stateReview.list ?? [], [stateReview.list]);
  console.log("myReviews :: ", stateReview)
//   const myReviews = useMemo(
//     () => stateReview.myList.filter((review) => review.member_id === me?.member_id),
//     [stateReview.list, me?.member_id]
//   );

  // 내가 작성한 커뮤니티 글만 필터링
  const myCommunities = useMemo(
    () => stateCommunity.list.filter((community) => community.member_id === me?.member_id),
    [stateCommunity.list, me?.member_id]
  );

  if (!me) {
    return (
      <div className={styles.loading}>
        <p>로딩 중...</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.grid}>
        {/* 왼쪽: 회원 정보 사이드바 */}
        <ProfileSidebar member={me} />

        {/* 오른쪽: 메인 콘텐츠 */}
        <div>
          {/* 에러 메시지 */}
          {stateMember?.error && (
            <div className={styles.error}>
              {stateMember.error}
            </div>
          )}

          {/* 내가 선택한 제한 아이템 섹션 */}
          <RestrictionsSection selectedIds={selectedIds} />

          {/* 내가 작성한 리뷰 섹션 */}
          <ReviewSection
            reviews={myReviews}
            currentPage={reviewPage}
            onPageChange={setReviewPage}
          />

          {/* 내가 작성한 커뮤니티 글 섹션 */}
          <CommunitySection
            communities={myCommunities}
            currentPage={communityPage}
            onPageChange={setCommunityPage}
          />
        </div>
      </div>
    </div>
  );
}
