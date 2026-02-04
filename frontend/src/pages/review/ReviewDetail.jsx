import { useContext, useEffect, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";
import { MemberContext } from "../../context/MemberContext";
import { ReviewDetail } from "../../components/review/ReviewDetail";
import styles from "./ReviewDetailPage.module.css";

function normalizeReview(raw) {
  if (!raw) return null;

  // 백엔드/프론트 필드명 흔들려도 최대한 안전하게 매핑
  const title = raw.review_title ?? raw.title ?? raw.subject ?? "";
  const content = raw.review_content ?? raw.content ?? raw.body ?? "";
  const rating = raw.rating ?? raw.star ?? raw.score ?? null;

  // 작성일
  const createdAt =
    raw.review_create ?? raw.created_at ?? raw.createdAt ?? raw.created ?? null;

  // 이미지
  // - raw.images: [{url:...}] 형태일 수도
  // - raw.image_urls: ["..."] 형태일 수도
  // - raw.images: ["..."]일 수도
  const images = Array.isArray(raw.image_urls)
    ? raw.image_urls
    : Array.isArray(raw.images)
      ? raw.images.map((x) => (typeof x === "string" ? x : x?.url)).filter(Boolean)
      : [];

  // ✅ menu_name
  const menuName = raw.menu_name ?? raw.menuName ?? raw.menu ?? "";

  // ✅ review_items: "3,7,12" | [3,7,12] | null  -> number[]
  const itemIds = (() => {
    const v = raw.review_items ?? raw.reviewItems ?? raw.item_ids ?? raw.itemIds;
    if (!v) return [];
    if (Array.isArray(v)) return v.map((x) => Number(x)).filter(Number.isFinite);
    if (typeof v === "string") {
      return v
        .split(",")
        .map((s) => Number(String(s).trim()))
        .filter(Number.isFinite);
    }
    return [];
  })();

  return {
    id: raw.id ?? raw.review_id ?? raw.reviewId ?? null,
    title,
    content,
    rating,
    createdAt,
    images,
    itemIds,
    menuName,
    raw, // 필요하면 디버깅용
  };
}

export default function ReviewDetailPage() {
  const { id } = useParams();
  const nav = useNavigate();
  const { stateReview, reviewActions } = useContext(ReviewContext);
  const { stateMember } = useContext(MemberContext);

  useEffect(() => {
    if (!id) return;
    reviewActions.fetchDetail(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const review = useMemo(
    () => normalizeReview(stateReview.detail),
    [stateReview.detail]
  );

  // 컨텐츠에 사용 중인지 확인 (실제로는 백엔드에서 체크해야 함)
  // 여기서는 임시로 review.used_in_content 필드가 있다고 가정
  const isUsedInContent = review?.raw?.used_in_content || false;

  const handleEdit = () => {
    nav(`/review/${id}/edit`);
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>리뷰 상세</h2>

        <button onClick={() => nav("/review")} className={styles.backButton}>
          목록으로
        </button>
      </div>

      {stateReview.error && (
        <div className={styles.error}>
          {stateReview.error}
        </div>
      )}

      {stateReview.loading && (
        <div className={styles.loading}>
          로딩 중...
        </div>
      )}

      {!stateReview.loading && review && (
        <ReviewDetail
          review={review}
          onEdit={handleEdit}
          canEdit={true}
          isUsedInContent={isUsedInContent}
          currentMemberId={stateMember.me?.member_id}
        />
      )}
    </div>
  );
}