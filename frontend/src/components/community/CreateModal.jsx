import { useEffect, useMemo, useState } from "react";
import Modal from "../common/Modal";
import styles from "../../styles/CreateModal.css";
import TemplateRadioCard from "./TemplateRadioCard";

export default function CreateModal({
  isOpen,
  onClose,
  stateReview,
  reviewActions,
  onConfirm,
  saving = false,
}) {
  const [templateId, setTemplateId] = useState(1);
  const [selectedIds, setSelectedIds] = useState([]);

  const reviews = stateReview.list ?? [];

  const isReviewActive = (r) =>
    (r.available ?? r.is_active ?? r.isActive) === true;

  const activeReviews = useMemo(() => reviews.filter(isReviewActive), [reviews]);

  const activeIds = useMemo(
    () => activeReviews.map((r) => r.review_id ?? r.id),
    [activeReviews]
  );

  useEffect(() => {
    if (!isOpen) return;

    if (reviews.length === 0 && !stateReview.loading) {
      reviewActions.fetchList();
    }

    setTemplateId(1);
    setSelectedIds([]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;

    if (templateId === 2) setSelectedIds(activeIds);
    else setSelectedIds([]);
  }, [templateId, activeIds.join(","), isOpen]);

  const toggleSelect = (id, isActive) => {
    if (!isActive) return;
    if (templateId === 2) return;

    setSelectedIds((prev) => {
      const has = prev.includes(id);
      if (has) return prev.filter((v) => v !== id);
      if (prev.length >= 3) return prev;
      return [...prev, id];
    });
  };

  const canSubmit =
    templateId === 1
      ? activeReviews.length >= 3 && selectedIds.length === 3
      : activeIds.length >= 3;

  const handleConfirm = () => {
    if (!canSubmit || saving) return;

    const reviewIds = templateId === 2 ? activeIds : selectedIds;
    onConfirm?.({ templateId, reviewIds });
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="AI 이미지 생성">
      <p className={styles.desc}>Choose a template</p>

      <div className="templateGrid">
        <TemplateRadioCard
          value={1}
          checked={templateId === 1}
          onChange={setTemplateId}
          imgSrc="/template2.png"
          title="Template 1 (Journal)"
          description="Select exactly 3 ACTIVE reviews"
        />

        <TemplateRadioCard
          value={2}
          checked={templateId === 2}
          onChange={setTemplateId}
          imgSrc="/template1.png"
          title="Template 2 (Map)"
          description="Uses ALL ACTIVE reviews"
        />
      </div>

      <div className="section" style={{ marginTop: 12 }}>
        <div className="sectionTitle">
          Total reviews ({reviews.length}) / ACTIVE ({activeReviews.length})
        </div>

        {stateReview.loading && (
          <div className={styles.loading}>리뷰 불러오는 중...</div>
        )}

        {!stateReview.loading && reviews.length === 0 && (
          <div className={styles.empty}>리뷰가 없습니다.</div>
        )}

        {!stateReview.loading && reviews.length > 0 && (
          <>
            {templateId === 1 && (
              <>
                <div className={styles.hint}>
                  Chosen 3 reviews will be used ({selectedIds.length}/3)
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
                            onChange={() => toggleSelect(id, isActive)}
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

            {templateId === 2 && (
              <div className={styles.hint}>
                Template 2 uses the location of ALL ACTIVE reviews to create a
                roadmap.
              </div>
            )}
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