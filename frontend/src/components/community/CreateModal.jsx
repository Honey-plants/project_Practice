import { useContext, useEffect, useMemo, useState } from "react";
import Modal from "../common/Modal";
import styles from "../../styles/CreateModal.module.css";
import { MemberContext } from "../../context/MemberContext";

export default function CreateModal({
  isOpen,
  onClose,
  stateReview,
  reviewActions,
  onConfirm,
  saving = false,
}) {
  const { stateMember } = useContext(MemberContext);
  const myMemberId = stateMember?.me?.member_id;

  const [templateId, setTemplateId] = useState(1);
  const [selectedIds, setSelectedIds] = useState([]);

  const myReviews = useMemo(() => stateReview.list ?? [], [stateReview.list]);
  const isReviewActive = (r) => (r.available ?? r.is_active ?? r.isActive) === true;

  const activeReviews = useMemo(() => myReviews.filter(isReviewActive), [myReviews]);
  const activeIds = useMemo(
    () => activeReviews.map((r) => r.review_id ?? r.id),
    [activeReviews]
  );

  useEffect(() => {
    if (!isOpen) return;

    setTemplateId(1);
    setSelectedIds([]);

    if (!myMemberId) return;

    // 모달 열기마다 반드시 본인 리뷰만 새로 가져옴
    reviewActions.fetchMyList?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return;
    setSelectedIds(templateId === 2 ? activeIds : []);
  }, [templateId, activeIds.join(","), isOpen]);

  const toggleSelect = (id, isActive) => {
    if (!isActive || templateId === 2) return;
    setSelectedIds((prev) => {
      const has = prev.includes(id);
      if (has) return prev.filter((v) => v !== id);
      if (prev.length >= 3) return prev;
      return [...prev, id];
    });
  };

  const canSubmit =
    templateId === 1 ? activeReviews.length >= 3 && selectedIds.length === 3 : activeIds.length > 0;

  const handleConfirm = () => {
    if (!canSubmit || saving) return;
    onConfirm?.({ templateId, reviewIds: templateId === 2 ? activeIds : selectedIds });
  };

  return (
    <Modal isOpen={isOpen} onClose={saving ? undefined : onClose} title="AI 이미지 생성">
      {/* 생성 중 로딩 오버레이 — 모든 조작 차단 */}
      {saving && (
        <div className={styles.loadingOverlay}>
          <div className={styles.loadingSpinner}></div>
          <p className={styles.loadingText}>AI 이미지 생성 중...</p>
        </div>
      )}

      <p className={styles.desc}>Choose a template</p>

      {/* ✅ Template 선택 UI (컴포넌트 없이 inline) */}
      <div className={styles.templateRow}>
        <label className={`${styles.templateItem} ${templateId === 1 ? styles.active : ""}`}>
          <input
            type="radio"
            name="tpl"
            checked={templateId === 1}
            onChange={() => setTemplateId(1)}
          />
          <img src="/template1.png" alt="Template 1" />
          <div>
            <b>Template 1 (Journal)</b>
            <div className={styles.small}>Select exactly 3 ACTIVE reviews</div>
          </div>
        </label>

        <label className={`${styles.templateItem} ${templateId === 2 ? styles.active : ""}`}>
          <input
            type="radio"
            name="tpl"
            checked={templateId === 2}
            onChange={() => setTemplateId(2)}
          />
          <img src="/template2.png" alt="Template 2" />
          <div>
            <b>Template 2 (Map)</b>
            <div className={styles.small}>Uses ALL ACTIVE reviews</div>
          </div>
        </label>
      </div>

      <div className={styles.section}>
        <div className={styles.sectionTitle}>
          Total reviews ({myReviews.length}) / ACTIVE ({activeReviews.length})
        </div>

        {!myMemberId && <div className={styles.empty}>로그인이 필요합니다.</div>}
        {myMemberId && stateReview.loading && <div className={styles.loading}>리뷰 불러오는 중...</div>}
        {myMemberId && !stateReview.loading && myReviews.length === 0 && (
          <div className={styles.empty}>리뷰가 없습니다.</div>
        )}

        {myMemberId && !stateReview.loading && myReviews.length > 0 && templateId === 1 && (
          <>
            <div className={styles.hint}>
              Chosen 3 reviews will be used ({selectedIds.length}/3)
            </div>

            <ul className={styles.reviewList}>
              {myReviews.map((r) => {
                const id = r.review_id ?? r.id;
                const title = r.review_title ?? r.title ?? "(no title)";
                const isActive = isReviewActive(r);
                const checked = selectedIds.includes(id);

                return (
                  <li key={id} className={`${styles.reviewItem} ${!isActive ? styles.inactive : ""}`}>
                    <label className={styles.checkboxRow}>
                      <input
                        type="checkbox"
                        checked={checked}
                        disabled={!isActive}
                        onChange={() => toggleSelect(id, isActive)}
                      />
                      <span className={styles.reviewTitle}>
                        {title}
                        {!isActive && <span className={styles.inactiveTag}> (INACTIVE)</span>}
                      </span>
                    </label>
                  </li>
                );
              })}
            </ul>
          </>
        )}

        {myMemberId && !stateReview.loading && myReviews.length > 0 && templateId === 2 && (
          <div className={styles.hint}>
            Template 2 uses the location of ALL ACTIVE reviews to create a roadmap. ({activeIds.length}개)
          </div>
        )}
      </div>

      <div className={styles.actions}>
        <button type="button" onClick={onClose} disabled={saving} className={styles.btnGhost}>
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
