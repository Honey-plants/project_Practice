import { useEffect, useMemo, useState } from "react";
import Modal from "../common/Modal";
import styles from "../../styles/CreateModal.css";

export default function CreateModal({
  isOpen,
  onClose,
  stateReview,
  reviewActions,
  onConfirm,
  saving = false,
}) {
  const [selectedIds, setSelectedIds] = useState([]);

  const reviews = stateReview.list ?? [];

  const isReviewActive = (r) =>
    (r.available ?? r.is_active ?? r.isActive) === true;

  const activeReviews = useMemo(
    () => reviews.filter(isReviewActive),
    [reviews]
  );

  useEffect(() => {
    if (!isOpen) return;

    if (!stateReview.loading) {
      reviewActions.fetchList();
    }

    setSelectedIds([]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((v) => v !== id);
      if (prev.length >= 3) return prev;
      return [...prev, id];
    });
  };

  const canSubmit = selectedIds.length === 3;

  const handleConfirm = () => {
    if (!canSubmit || saving) return;
    onConfirm?.({ reviewIds: selectedIds });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Select Reviews">
      <p className={styles.desc}>
        Select exactly <b>3 ACTIVE</b> reviews
      </p>

      <div className="section" style={{ marginTop: 12 }}>
        <div className="sectionTitle">
          ACTIVE reviews ({activeReviews.length})
        </div>

        {stateReview.loading && (
          <div className={styles.loading}>리뷰 불러오는 중...</div>
        )}

        {!stateReview.loading && (
          <>
            <div className={styles.hint}>
              Selected ({selectedIds.length}/3)
            </div>

            <ul className="reviewList">
              {reviews.map((r) => {
                const id = r.review_id ?? r.id;
                const title = r.review_title ?? r.title ?? "(no title)";
                const isActive = isReviewActive(r);
                const checked = selectedIds.includes(id);

                return (
                  <li
                    key={id}
                    className={`${styles.reviewItem} ${
                      !isActive ? styles.inactive : ""
                    }`}
                  >
                    <label className="checkboxRow">
                      <input
                        type="checkbox"
                        checked={checked}
                        disabled={!isActive}
                        onChange={() => toggleSelect(id)}
                      />
                      <span className="reviewTitle">
                        {title}
                        {!isActive && (
                          <span className="inactiveTag"> (INACTIVE)</span>
                        )}
                      </span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </>
        )}
      </div>

      <div className={styles.actions}>
        <button type="button" onClick={onClose} className={styles.btnGhost}>
          Cancel
        </button>

        <button
          type="button"
          onClick={handleConfirm}
          disabled={!canSubmit || saving}
          className={styles.btnPrimary}
        >
          {saving ? "Creating..." : "Create"}
        </button>
      </div>
    </Modal>
  );
}
