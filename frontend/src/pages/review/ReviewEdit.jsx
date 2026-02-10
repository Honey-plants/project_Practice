import { useContext, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";
import styles from "./ReviewEdit.module.css";

export default function ReviewEdit() {
  const { id } = useParams();
  const nav = useNavigate();
  const { stateReview, reviewActions } = useContext(ReviewContext);

  const [content, setContent] = useState("");
  const [isUsedInContent, setIsUsedInContent] = useState(false);

  useEffect(() => {
    (async () => {
      const d = await reviewActions.fetchDetail(id);
      if (d) {
        setContent(d.review_content ?? d.content ?? d.body ?? "");
        setIsUsedInContent(d.used_in_content || false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onSave = async (e) => {
    e.preventDefault();

    if (isUsedInContent) {
      alert("This review is in use with content and cannot be modified.");
      return;
    }

   
    const trimmedContent = (content || "").trim();

    if (!trimmedContent) return alert("Please enter the contents.");

    try {
      await reviewActions.updateContent(id, trimmedContent);
      nav(`/review/${id}`);
    } catch (err) {
      alert(err?.message || "Failed to eidt");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h2 className={styles.title}>Review Edit</h2>
        <button onClick={() => nav(`/review/${id}`)} className={styles.cancelButton}>
          Cancel
        </button>
      </div>

      {stateReview.error && (
        <div className={styles.error}>
          {stateReview.error}
        </div>
      )}

      {isUsedInContent && (
        <div className={styles.warning}>
          ⚠️ This review is in use with content and cannot be edit.
        </div>
      )}

      <form onSubmit={onSave} className={styles.form}>
        <div className={styles.formGroup}>
          <label className={styles.label}>
            contents
          </label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Please enter your review"
            rows={12}
            disabled={isUsedInContent}
            className={styles.textarea}
          />
        </div>

        <button type="submit" disabled={isUsedInContent} className={styles.submitButton}>
          {isUsedInContent ? "Unable to modify" : "save"}
        </button>
      </form>
    </div>
  );
}
