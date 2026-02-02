import React, { useContext, useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";

export default function ReviewEdit() {
  const { id } = useParams();
  const nav = useNavigate();
  const { stateReview, reviewActions } = useContext(ReviewContext);

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isUsedInContent, setIsUsedInContent] = useState(false);

  useEffect(() => {
    (async () => {
      const d = await reviewActions.fetchDetail(id);
      if (d) {
        setTitle(d.review_title ?? d.title ?? "");
        setContent(d.review_content ?? d.content ?? d.body ?? "");
        setIsUsedInContent(d.used_in_content || false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onSave = async (e) => {
    e.preventDefault();

    if (isUsedInContent) {
      alert("이 리뷰는 컨텐츠에 사용 중이어서 수정할 수 없습니다.");
      return;
    }

    const trimmedTitle = (title || "").trim();
    const trimmedContent = (content || "").trim();

    if (!trimmedTitle) return alert("제목을 입력해주세요.");
    if (!trimmedContent) return alert("내용을 입력해주세요.");

    try {
      await reviewActions.updateContent(id, trimmedContent);
      nav(`/review/${id}`);
    } catch (err) {
      alert(err?.message || "수정 실패");
    }
  };

  return (
    <div style={{ padding: "20px", maxWidth: "900px", margin: "0 auto" }}>
      <div style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        marginBottom: "24px"
      }}>
        <h2 style={{ margin: 0, fontSize: "24px", fontWeight: "700" }}>리뷰 수정</h2>
        <button
          onClick={() => nav(`/review/${id}`)}
          style={{
            padding: "8px 16px",
            background: "#6c757d",
            color: "white",
            border: "none",
            borderRadius: "6px",
            cursor: "pointer",
            fontSize: "14px",
            fontWeight: "600"
          }}
        >
          취소
        </button>
      </div>

      {stateReview.error && (
        <div style={{
          padding: "12px",
          background: "#f8d7da",
          color: "#721c24",
          borderRadius: "6px",
          marginBottom: "16px",
          border: "1px solid #f5c6cb"
        }}>
          {stateReview.error}
        </div>
      )}

      {isUsedInContent && (
        <div style={{
          padding: "16px",
          background: "#fff3cd",
          color: "#856404",
          borderRadius: "8px",
          marginBottom: "16px",
          border: "1px solid #ffc107",
          fontWeight: "600"
        }}>
          ⚠️ 이 리뷰는 컨텐츠에 사용 중이어서 수정할 수 없습니다.
        </div>
      )}

      <form onSubmit={onSave} style={{
        display: "grid",
        gap: 16,
        background: "white",
        padding: "24px",
        borderRadius: "12px",
        border: "1px solid #e0e0e0"
      }}>
        <div>
          <label style={{ display: "block", marginBottom: 8, fontWeight: 600, fontSize: 15 }}>
            제목
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="리뷰 제목을 입력하세요"
            disabled={isUsedInContent}
            style={{
              width: "100%",
              padding: "12px",
              borderRadius: "6px",
              border: "1px solid #ddd",
              fontSize: "14px",
              background: isUsedInContent ? "#f8f9fa" : "white"
            }}
          />
        </div>

        <div>
          <label style={{ display: "block", marginBottom: 8, fontWeight: 600, fontSize: 15 }}>
            내용
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="리뷰 내용을 입력하세요"
            rows={12}
            disabled={isUsedInContent}
            style={{
              width: "100%",
              padding: "12px",
              borderRadius: "6px",
              border: "1px solid #ddd",
              fontSize: "14px",
              resize: "vertical",
              lineHeight: 1.6,
              background: isUsedInContent ? "#f8f9fa" : "white"
            }}
          />
        </div>

        <button
          type="submit"
          disabled={isUsedInContent}
          style={{
            padding: "12px 24px",
            borderRadius: "6px",
            fontSize: "16px",
            fontWeight: "600",
            border: "none",
            background: isUsedInContent ? "#ccc" : "#28a745",
            color: "white",
            cursor: isUsedInContent ? "not-allowed" : "pointer"
          }}
        >
          {isUsedInContent ? "수정 불가" : "저장"}
        </button>
      </form>
    </div>
  );
}
