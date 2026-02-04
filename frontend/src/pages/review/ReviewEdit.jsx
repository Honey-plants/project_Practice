import React, { useContext, useEffect, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";
import styles from "./ReviewEdit.module.css";

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
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>리뷰 수정</h2>
        <button onClick={() => nav(`/review/${id}`)} className={styles.cancelButton}>
          취소
        </button>
      </div>

      {stateReview.error && (
        <div className={styles.error}>
          {stateReview.error}
        </div>
      )}

      {isUsedInContent && (
        <div className={styles.warning}>
          ⚠️ 이 리뷰는 컨텐츠에 사용 중이어서 수정할 수 없습니다.
        </div>
      )}

      <form onSubmit={onSave} className={styles.form}>
        {/* <div className={styles.formGroup}>
          <label className={styles.label}>
            제목
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="리뷰 제목을 입력하세요"
            disabled={isUsedInContent}
            className={styles.input}
          />
        </div> */}

        <div className={styles.formGroup}>
          <label className={styles.label}>
            내용
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="리뷰 내용을 입력하세요"
            rows={12}
            disabled={isUsedInContent}
            className={styles.textarea}
          />
        </div>

        <button type="submit" disabled={isUsedInContent} className={styles.submitButton}>
          {isUsedInContent ? "수정 불가" : "저장"}
        </button>
      </form>
    </div>
  );
}
