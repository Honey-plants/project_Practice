import './ReviewCard.css';
import { useNavigate } from "react-router-dom";

function ReviewItem({ review }) {
  const nav = useNavigate();

  // 데이터 정규화 (API 응답 형식이 다를 수 있으므로)
  const reviewId = review.review_id || review.id;
  const title = review.review_title || review.title || review.subject || "(제목 없음)";
  const content = review.review_content || review.content || "";
  const rating = review.rating || 0;
  const location = review.location || "";
  const imageUrl = review.image_urls?.[0] || review.image_url || null;
  const tags = review.allergy_tags || review.tags || [];
  const createdAt = review.created_at || "";

  const handleClick = () => {
    nav(`/review/${reviewId}`);
  };

  // 별점 렌더링 함수
  const renderStars = (rating) => {
    const stars = [];
    for (let i = 1; i <= 5; i++) {
      stars.push(
        <span key={i} style={{ color: i <= rating ? "#ffc107" : "#ddd", fontSize: "16px" }}>
          ★
        </span>
      );
    }
    return stars;
  };

  return (
    <div
      onClick={handleClick}
      className="review-card"
      style={{
        cursor: "pointer",
        border: "1px solid #e0e0e0",
        borderRadius: "12px",
        overflow: "hidden",
        transition: "transform 0.2s, box-shadow 0.2s",
        background: "white",
        boxShadow: "0 2px 4px rgba(0,0,0,0.05)"
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = "translateY(-6px)";
        e.currentTarget.style.boxShadow = "0 8px 16px rgba(0,0,0,0.12)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = "translateY(0)";
        e.currentTarget.style.boxShadow = "0 2px 4px rgba(0,0,0,0.05)";
      }}
    >
      {imageUrl ? (
        <img
          src={imageUrl}
          alt={title}
          style={{
            width: "100%",
            height: "200px",
            objectFit: "cover"
          }}
        />
      ) : (
        <div style={{
          width: "100%",
          height: "200px",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "white",
          fontSize: "48px"
        }}>
          🍽️
        </div>
      )}

      <div style={{ padding: "16px" }}>
        {/* 제목 */}
        <h3 style={{
          margin: "0 0 8px 0",
          fontSize: "18px",
          fontWeight: "600",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          color: "#212529"
        }}>
          {title}
        </h3>

        {/* 별점 */}
        {rating > 0 && (
          <div style={{ marginBottom: "8px", display: "flex", alignItems: "center", gap: "6px" }}>
            {renderStars(rating)}
            <span style={{ fontSize: "14px", color: "#666", marginLeft: "4px" }}>
              ({rating}.0)
            </span>
          </div>
        )}

        {/* 내용 미리보기 */}
        {content && (
          <p style={{
            margin: "0 0 8px 0",
            fontSize: "14px",
            color: "#666",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap"
          }}>
            {content}
          </p>
        )}

        {/* 위치 정보 */}
        {location && (
          <div style={{
            fontSize: "12px",
            color: "#999",
            marginBottom: "8px",
            display: "flex",
            alignItems: "center",
            gap: "4px"
          }}>
            <span>📍</span>
            <span>{location}</span>
          </div>
        )}

        {/* 알레르기 태그 */}
        {tags.length > 0 && (
          <div style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "6px",
            marginTop: "12px"
          }}>
            {tags.map((tag) => (
              <span
                key={tag}
                style={{
                  padding: "4px 10px",
                  background: "#fff3cd",
                  color: "#856404",
                  borderRadius: "12px",
                  fontSize: "11px",
                  fontWeight: "500",
                  border: "1px solid #ffeaa7"
                }}
              >
                ⚠️ {tag}
              </span>
            ))}
          </div>
        )}

        {/* 작성일 */}
        {createdAt && (
          <div style={{
            fontSize: "11px",
            color: "#aaa",
            marginTop: "12px",
            paddingTop: "8px",
            borderTop: "1px solid #f0f0f0"
          }}>
            {new Date(createdAt).toLocaleDateString('ko-KR')}
          </div>
        )}
      </div>
    </div>
  );
}

export default ReviewItem;