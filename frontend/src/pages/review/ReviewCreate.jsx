import React, { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";

export default function ReviewCreate() {
  const nav = useNavigate();
  const { reviewActions } = useContext(ReviewContext);

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const created = await reviewActions.create({ title, content });
      const id = created?.id ?? created?.review_id;
      nav(id ? `/review/${id}` : "/review");
    } catch (e2) {
      setError(e2.message || "작성 실패");
    }
  };

  return (
    <div style={{ padding: 16, maxWidth: 720 }}>
      <h2>New Review</h2>

      <form onSubmit={onSubmit} style={{ display: "grid", gap: 10 }}>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="title" />
        <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="content" rows={8} />
        <button type="submit">Create</button>
      </form>

      {error && <div className="errorBox">{error}</div>}
    </div>
  );
}