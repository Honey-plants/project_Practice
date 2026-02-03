import './ReviewCard.css';
import { useNavigate } from "react-router-dom";
import { useContext, useMemo, useState } from "react";
import { MetaContext } from "../../context/MetaContext";

function ReviewItem({ review }) {
  const nav = useNavigate();
  const { stateMeta } = useContext(MetaContext);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  // 데이터 정규화 (API 응답 형식이 다를 수 있으므로)
  const reviewId = review.review_id || review.id;
  const title = review.review_title || review.title || review.subject || "(제목 없음)";
  const content = review.review_content || review.content || "";
  const rating = review.rating || 0;
  const imageUrls = review.image_urls || (review.image_url ? [review.image_url] : []);

  // menu_name이 배열이면 join, 문자열이면 그대로, 없으면 빈 문자열
  const menuName = Array.isArray(review.menu_name)
    ? review.menu_name.join(',')
    : (review.menu_name || "");

  const createdAt = review.created_at || review.create_at || "";

  // 아이템 ID에 해당하는 라벨 찾기
  const itemLabels = useMemo(() => {
    const reviewItems = review.review_items || [];
    const itemIds = typeof reviewItems === 'string'
      ? reviewItems.split(',').map(id => Number(id.trim()))
      : Array.isArray(reviewItems)
      ? reviewItems.map(id => Number(id))
      : [];

    if (!itemIds.length || !stateMeta.restrictions.length) return [];

    const allItems = stateMeta.restrictions.flatMap(cat => cat.items || []);
    return itemIds
      .map(id => {
        const item = allItems.find(item => item.item_id === id);
        return item ? (item.item_label_ko || item.item_label_en || `Item #${id}`) : `Item #${id}`;
      });
  }, [review.review_items, stateMeta.restrictions]);

  const handleClick = () => {
      console.log("클릭 reviewId :: ", {reviewId})
      nav(`/review/${reviewId}`);
  };

  const handlePrevImage = (e) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev === 0 ? imageUrls.length - 1 : prev - 1));
  };

  const handleNextImage = (e) => {
    e.stopPropagation();
    setCurrentImageIndex((prev) => (prev === imageUrls.length - 1 ? 0 : prev + 1));
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
    <div onClick={handleClick} className="review-card">
      {imageUrls.length > 0 ? (
        <div className="review-card-image-container">
          <img
            src={imageUrls[currentImageIndex]}
            alt={title}
            className="review-card-image"
          />
          {imageUrls.length > 1 && (
            <>
              <button
                onClick={handlePrevImage}
                className="image-nav-btn prev"
              >
                ‹
              </button>
              <button
                onClick={handleNextImage}
                className="image-nav-btn next"
              >
                ›
              </button>
              <div className="image-indicator">
                {currentImageIndex + 1} / {imageUrls.length}
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="review-card-no-image">
          🍽️
        </div>
      )}

      <div className="review-card-content">
        {/* 메뉴 이름 */}
        {menuName && (
          <div className="menu-names-container">
            {menuName.split(',').map((menu, idx) => (
              <div key={idx} className="menu-name-tag">
                🍽️ {menu.replace(/["[\]]/g, '').trim()}
              </div>
            ))}
          </div>
        )}

        {/* 제목 */}
        <h3 className="review-card-title">
          {title}
        </h3>

        {/* 별점 */}
        {rating > 0 && (
          <div className="review-card-rating">
            {renderStars(rating)}
            <span className="rating-text">
              ({rating}.0)
            </span>
          </div>
        )}

        {/* 내용 미리보기 */}
        {content && (
          <p className="review-card-preview">
            {content}
          </p>
        )}

        {/* 제한사항 아이템 태그 */}
        {itemLabels.length > 0 && (
          <div className="item-labels-container">
            {itemLabels.map((label, idx) => (
              <span key={idx} className="item-label-tag">
                ⚠️ {label}
              </span>
            ))}
          </div>
        )}

        {/* 작성일 */}
        {createdAt && (
          <div className="review-card-date">
            {new Date(createdAt).toLocaleDateString('ko-KR')}
          </div>
        )}
      </div>
    </div>
  );
}

export default ReviewItem;
