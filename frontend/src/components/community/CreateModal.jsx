import { useEffect, useMemo, useState } from "react";
import Modal from "../common/Modal";
import styles from "../../styles/CreateModal.module.css";

export default function CreateModal({
  isOpen,
  onClose,
  stateReview,
  reviewActions,
  templateId,
  initialSelectedIds = [],
  onConfirm,
  saving = false,
}) {
  const [selectedIds, setSelectedIds] = useState([]);

  const myReviews = useMemo(() => stateReview.list ?? [], [stateReview.list]);

  const activeReviews = useMemo(
    () =>
      myReviews.filter(
        (r) => (r.available ?? r.is_active ?? r.isActive) === true
      ),
    [myReviews]
  );

  useEffect(() => {
    if (!isOpen) return;

    // only Template 2 uses selection
    if (templateId !== 1) {
      setSelectedIds([]);
      return;
    }

    if (!stateReview.loading) {
      reviewActions.fetchMyList();
    }

    setSelectedIds(initialSelectedIds);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, templateId]);

  const toggleSelect = (id) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) return prev.filter((v) => v !== id);
      if (prev.length >= 3) return prev;
      return [...prev, id];
    });
  };

  const canSubmit = templateId === 1 && selectedIds.length > 0;

  const handleConfirm = () => {
    if (!canSubmit || saving) return;
    onConfirm?.({ reviewIds: selectedIds });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Select Reviews">
      {templateId !== 1 ? (
        <div className={styles.empty}>
          Review selection is only available for Template 2.
        </div>
      ) : (
        <>
          <p className={styles.desc}>Select ACTIVE reviews</p>

          <div className="section">
            <div className="sectionTitle">
              ACTIVE reviews ({activeReviews.length})
            </div>

            {stateReview.loading && (
              <div className={styles.loading}>리뷰 불러오는 중...</div>
            )}

            {!stateReview.loading && activeReviews.length === 0 && (
              <div className={styles.empty}>ACTIVE 리뷰가 없습니다.</div>
            )}

            {!stateReview.loading && activeReviews.length > 0 && (
              <>
                <div className={styles.hint}>
                  Selected ({selectedIds.length})
                </div>

                <ul className="reviewList">
                  {activeReviews.map((r) => {
                    const id = r.review_id ?? r.id;
                    const title = r.review_title ?? r.title ?? "(no title)";
                    const checked = selectedIds.includes(id);

                    return (
                      <li key={id} className={styles.reviewItem}>
                        <label className="checkboxRow">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleSelect(id)}
                          />
                          <span className="reviewTitle">{title}</span>
                        </label>
                      </li>
                    );
                  })}
                </ul>
              </>
            )}
          </div>

          <div className={styles.actions}>
            <button onClick={onClose} className={styles.btnGhost}>
              Back
            </button>
            <button
              onClick={handleConfirm}
              disabled={!canSubmit || saving}
              className={styles.btnPrimary}
            >
              Select Reviews
            </button>
          </div>
        </>
      )}
    </Modal>
  );
}
