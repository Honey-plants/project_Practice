import React from "react";
import { useNavigate } from "react-router-dom";
import ReviewCreateForm from "../../components/review/ReviewCreateForm";

export default function ReviewCreate() {
  const navigate = useNavigate();

  const handleCreated = (reviewData) => {
    console.log("리뷰 생성 완료:", reviewData);

    // 2초 후 리뷰 리스트 페이지로 이동
    setTimeout(() => {
      navigate("/review");
    }, 2000);
  };

  return (
    <div style={{
      minHeight: "100vh",
      background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      padding: "40px 20px"
    }}>
      <div style={{
        maxWidth: "900px",
        margin: "0 auto"
      }}>
        {/* 상단 헤더 */}
        <div style={{
          marginBottom: "24px",
          textAlign: "center",
          color: "white"
        }}>
          <h1 style={{
            fontSize: "36px",
            fontWeight: "800",
            margin: "0 0 8px 0",
            textShadow: "2px 2px 4px rgba(0,0,0,0.2)"
          }}>
            🍽️ 새 리뷰 작성
          </h1>
          <p style={{
            fontSize: "16px",
            margin: 0,
            opacity: 0.95
          }}>
            영수증을 업로드하고 맛있었던 경험을 공유해주세요!
          </p>
        </div>

        {/* 뒤로가기 버튼 */}
        <div style={{ marginBottom: "16px" }}>
          <button
            onClick={() => navigate("/review")}
            style={{
              padding: "10px 20px",
              background: "rgba(255, 255, 255, 0.2)",
              color: "white",
              border: "1px solid white",
              borderRadius: "8px",
              cursor: "pointer",
              fontWeight: "600",
              fontSize: "14px",
              backdropFilter: "blur(10px)",
              transition: "all 0.2s"
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.3)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.2)";
            }}
          >
            ← 리뷰 목록으로 돌아가기
          </button>
        </div>

        {/* 리뷰 작성 폼 */}
        <ReviewCreateForm onCreated={handleCreated} />
      </div>
    </div>
  );
}
