import './ReviewCard.css';
import { useNavigate } from "react-router-dom";

function ReviewItem({ review }) {
  const nav = useNavigate();

  return (
    <div onClick={() => nav(`/reviews/${review.review_id}`)}>
      <img
        src={review.image_urls[0]}
        alt="리뷰 이미지"
        width={200}
      />

      <h3>{review.review_title}</h3>

      <div>
        {review.allergy_tags.map((tag) => (
          <span key={tag}>#{tag} </span>
        ))}
      </div>
    </div>
  );
}

export default ReviewItem;
