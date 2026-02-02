import React, { useContext, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";
import ReviewItem from "../../components/review/ReviewCard"

// 임시 목 데이터 - API 연동 전 테스트용
const MOCK_DATA = [
  {
    review_id: 1,
    review_title: "맛있는 비빔밥 후기",
    review_content: "영양가 있고 맛있었습니다!",
    rating: 5,
    location: "서울시 강남구",
    image_urls: ["https://via.placeholder.com/300x200/FFB6C1/000000?text=Bibimbap"],
    allergy_tags: ["땅콩", "우유"],
    created_at: "2024-01-15"
  },
  {
    review_id: 2,
    review_title: "김치찌개 리뷰",
    review_content: "얼큰하고 좋았어요",
    rating: 4,
    location: "서울시 서초구",
    image_urls: ["https://via.placeholder.com/300x200/87CEEB/000000?text=Kimchi+Jjigae"],
    allergy_tags: ["계란"],
    created_at: "2024-01-14"
  },
  {
    review_id: 3,
    review_title: "파스타 맛집 발견",
    review_content: "크림 파스타가 일품이었습니다",
    rating: 5,
    location: "서울시 마포구",
    image_urls: [],
    allergy_tags: ["밀", "우유"],
    created_at: "2024-01-13"
  }
];

export default function ReviewList() {
  const { stateReview, reviewActions } = useContext(ReviewContext);

  const [useMockData, setUseMockData] = useState(false);
//   const [useMockData, setUseMockData] = useState(true); // Mock 데이터 사용 여부

  useEffect(() => {
    // API 연동 모드일 때만 리스트 fetch
    if (!useMockData) {
      reviewActions.fetchList();
    }
  }, [useMockData]);

  // 페이지 진입 시 한 번만 실행 - 새로고침 효과
  useEffect(() => {
    if (!useMockData) {
      reviewActions.fetchList();
    }
  }, []);

  // Mock 데이터 사용 시
  const displayList = useMockData ? MOCK_DATA : stateReview.list;
  const displayLoading = useMockData ? false : stateReview.loading;
  const displayError = useMockData ? "" : stateReview.error;

  return (
    <div style={{ padding: "20px", maxWidth: "1200px", margin: "0 auto" }}>
      {/* Mock 데이터 토글 버튼 */}
      <div style={{
        marginBottom: "16px",
        padding: "12px",
        background: "#fff3cd",
        borderRadius: "8px",
        border: "1px solid #ffc107"
      }}>
        <label style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: "8px" }}>
          <input
            type="checkbox"
            checked={useMockData}
            onChange={(e) => setUseMockData(e.target.checked)}
            style={{ cursor: "pointer" }}
          />
          <span style={{ fontWeight: "500" }}>
            Mock 데이터 사용 (API 연결 전 테스트용)
          </span>
        </label>
      </div>

      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "24px"
      }}>
        <h1 style={{ margin: 0, fontSize: "28px", fontWeight: "700" }}>리뷰 목록</h1>
        <Link
          to="/review/new"
          style={{
            padding: "10px 20px",
            background: "#007bff",
            color: "white",
            textDecoration: "none",
            borderRadius: "6px",
            fontWeight: "600",
            transition: "background 0.2s"
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = "#0056b3"}
          onMouseLeave={(e) => e.currentTarget.style.background = "#007bff"}
        >
          + 새 리뷰 작성
        </Link>
      </div>

      {displayError && (
        <div style={{
          padding: "16px",
          background: "#fee",
          color: "#c00",
          borderRadius: "8px",
          marginBottom: "20px",
          border: "1px solid #fcc"
        }}>
          <strong>오류 발생:</strong> {displayError}
        </div>
      )}

      {displayLoading && (
        <div style={{
          textAlign: "center",
          padding: "80px 20px",
          fontSize: "18px",
          color: "#666"
        }}>
          <div style={{
            display: "inline-block",
            width: "40px",
            height: "40px",
            border: "4px solid #f3f3f3",
            borderTop: "4px solid #007bff",
            borderRadius: "50%",
            animation: "spin 1s linear infinite"
          }}></div>
          <div style={{ marginTop: "16px" }}>로딩 중...</div>
        </div>
      )}

      {!displayLoading && displayList.length === 0 && (
        <div style={{
          textAlign: "center",
          padding: "80px 20px",
          color: "#999",
          background: "#f8f9fa",
          borderRadius: "8px"
        }}>
          <div style={{ fontSize: "48px", marginBottom: "16px" }}>📝</div>
          <div style={{ fontSize: "18px", marginBottom: "8px" }}>아직 리뷰가 없습니다</div>
          <div style={{ fontSize: "14px" }}>첫 번째 리뷰를 작성해보세요!</div>
        </div>
      )}

      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
        gap: "24px"
      }}>
        {displayList.map((review) => (
          <ReviewItem
            key={review.review_id || review.id}
            review={review}
          />
        ))}
      </div>
    </div>
  );
}