import { useContext, useEffect, useMemo } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";
import { ReviewDetail } from "../../components/common/ReviewDetail"

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

  return {
    id: raw.id ?? raw.review_id ?? raw.reviewId ?? null,
    title,
    content,
    rating,
    createdAt,
    images,
    raw, // 필요하면 디버깅용
  };
}

export default function ReviewDetailPage() {
  const { id } = useParams();
  const nav = useNavigate();
  const { stateReview, reviewActions } = useContext(ReviewContext);

  useEffect(() => {
    if (!id) return;
    reviewActions.fetchDetail(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const review = useMemo(
    () => normalizeReview(stateReview.detail),
    [stateReview.detail]
  );

  return (
    <div>
      <div style={{ padding: 16, maxWidth: 900, margin: "0 auto" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: 12,
          }}
        >
          <h2 style={{ margin: 0 }}>Review Detail</h2>

          <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
            <Link to="/review">Back</Link>
            <Link to={`/review/${id}/edit`}>Edit</Link>
          </div>
        </div>

        {stateReview.error && (
          <div className="errorBox" style={{ marginTop: 12 }}>
            {stateReview.error}
          </div>
        )}

        {stateReview.loading && <div style={{ marginTop: 12 }}>Loading...</div>}

        {!stateReview.loading && review && (
          <div style={{ marginTop: 16 }}>
            <ReviewDetail review={review} />
          </div>
        )}
      </div>
    </div>
  );
}