import React, { useContext, useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";

export default function ReviewEdit() {
  const { id } = useParams();
  const nav = useNavigate();
  const { stateReview, reviewActions } = useContext(ReviewContext);

  const [content, setContent] = useState("");

  useEffect(() => {
    (async () => {
      const d = await reviewActions.fetchDetail(id);
      if (d) {
        setContent(d.review_content ?? d.content ?? d.body ?? "");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onSave = async (e) => {
    e.preventDefault();
    const trimmed = (content || "").trim();
    if (!trimmed) return alert("내용을 입력해주세요.");

    try {
      await reviewActions.updateContent(id, trimmed);
      nav(`/review/${id}`);
    } catch (err) {
      alert(err?.message || "수정 실패");
    }
  };

  return (
    <div style={{ padding: 16, maxWidth: 900, margin: "0 auto" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2 style={{ margin: 0 }}>리뷰 내용 수정</h2>
        <Link to={`/review/${id}`}>Back</Link>
      </div>

      {stateReview.error && (
        <div className="errorBox" style={{ marginTop: 12 }}>
          {stateReview.error}
        </div>
      )}

      <form onSubmit={onSave} style={{ display: "grid", gap: 10, marginTop: 16 }}>
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="리뷰 내용을 수정하세요"
          rows={10}
          style={{ width: "100%", padding: 12, borderRadius: 8, border: "1px solid #ccc" }}
        />
        <button type="submit" style={{ padding: "10px 14px", borderRadius: 8 }}>
          저장
        </button>
      </form>
    </div>
  );
}
