import { useState, useContext, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import styles from "../../styles/Community.module.css";
import CommunityList from "../../components/community/CommunityList";
import CreateModal from "../../components/community/CreateModal";
import { CommunityContext } from "../../context/CommunityContext";
import { ReviewContext } from "../../context/ReviewContext";

export default function Community() {
  const nav = useNavigate();
  const { stateCommunity, communityActions } = useContext(CommunityContext);
  const { stateReview, reviewActions } = useContext(ReviewContext);

  const [onlyMine, setOnlyMine] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (onlyMine) {
      communityActions.fetchMyList();
    } else {
      communityActions.fetchList();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [onlyMine]);

  useEffect(() => {
    communityActions.fetchList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleConfirm = async ({ templateId, reviewIds }) => {
    setError("");
    setSaving(true);
    try {
      await communityActions.create({
        template_id: templateId,
        review_ids: reviewIds,
      });
      setIsModalOpen(false);
      setOnlyMine(true);
      communityActions.fetchMyList();
    } catch (e) {
      setError(e.message || "AI 이미지 생성에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Community</h1>

      {/* 버튼 영역 */}
      <div className={styles.buttonRow}>
        <button className={styles.button} onClick={() => setIsModalOpen(true)}>
          AI Image
        </button>
        <button className={styles.button} onClick={() => nav("/review/new")}>
          리뷰작성하기
        </button>
      </div>

      {error && <div className={styles.errorMsg}>{error}</div>}

      {/* 내 저널 필터 */}
      <div className={styles.filterRow}>
        <button
          className={`${styles.filterBtn} ${!onlyMine ? styles.filterActive : ""}`}
          onClick={() => setOnlyMine(false)}
        >
          전체
        </button>
        <button
          className={`${styles.filterBtn} ${onlyMine ? styles.filterActive : ""}`}
          onClick={() => setOnlyMine(true)}
        >
          내 저널
        </button>
      </div>

      {/* AI Image 생성 모달 — saving 중이면 닫기 불가 */}
      <CreateModal
        isOpen={isModalOpen}
        onClose={() => { if (!saving) setIsModalOpen(false); }}
        stateReview={stateReview}
        reviewActions={reviewActions}
        onConfirm={handleConfirm}
        saving={saving}
      />

      <CommunityList list={stateCommunity.list} loading={stateCommunity.loading} error={stateCommunity.error} />
    </div>
  );
}