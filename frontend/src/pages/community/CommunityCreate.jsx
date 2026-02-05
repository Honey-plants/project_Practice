import React, { useContext, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";
import { ReviewContext } from "../../context/ReviewContext";
import CreateModal from "../../components/community/CreateModal";
import "../../styles/CommunityCreate.css";

const TEMPLATES = [
  { id: 1, img: "/debug_out.png", title: "Template 1 · Journal", desc: "Pick 3 ACTIVE reviews and create a funny travel journal" },
  { id: 2, img: "/map_temp.png", title: "Template 2 · Map", desc: "Use ALL ACTIVE reviews to generate a travel map" },
];

export default function CommunityCreate() {
  const nav = useNavigate();
  const { communityActions } = useContext(CommunityContext);
  const { stateReview, reviewActions } = useContext(ReviewContext);

  const [templateId, setTemplateId] = useState(1);
  const [selectedReviewIds, setSelectedReviewIds] = useState([]);
  const [isOpen, setIsOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const isReviewActive = (r) => (r.available ?? r.is_active ?? r.isActive) === true;

  // ✅ ACTIVE 전체 ids (Map에서 사용)
  const activeIds = useMemo(() => {
    const list = stateReview.list ?? [];
    return list.filter(isReviewActive).map((r) => r.review_id ?? r.id);
  }, [stateReview.list]);

  const chosenTitles = useMemo(() => {
    const list = stateReview.list ?? [];
    const map = new Map(list.map((r) => [r.review_id ?? r.id, r]));
    return selectedReviewIds
      .map((id) => map.get(id))
      .filter(Boolean)
      .map((r) => r.review_title ?? r.title ?? "(no title)");
  }, [stateReview.list, selectedReviewIds]);

  const handleCreate = async () => {
    setSaving(true);
    setError("");

    try {
      // ✅ Journal(1)만 3개 선택 필수
      if (templateId === 1 && selectedReviewIds.length !== 3) {
        setError("Template 1 requires exactly 3 ACTIVE reviews.");
        return;
      }

      // ✅ Map(2)은 ACTIVE 전체를 보냄
      if (templateId === 2 && activeIds.length === 0) {
        setError("No ACTIVE reviews available for Map.");
        return;
      }

      await communityActions.create({
        template_id: templateId,
        review_ids: templateId === 1 ? selectedReviewIds : activeIds,
      });

      nav("/community");
    } catch (e) {
      setError(e?.message || "Generate AI image failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="communityCreate">
      <h2 className="pageTitle">New Community Post</h2>

      <div className="templateGrid">
        {TEMPLATES.map((t) => (
          <label
            key={t.id}
            className={`templateCard ${templateId === t.id ? "active" : ""}`}
            role="radio"
            aria-checked={templateId === t.id}
          >
            <input
              type="radio"
              name="template"
              checked={templateId === t.id}
              onChange={() => {
                setTemplateId(t.id);
                setSelectedReviewIds([]);
              }}
            />
            <img src={t.img} alt={t.title} />
            <div className="info">
              <div className="title">{t.title}</div>
              <div className="desc">{t.desc}</div>
            </div>
          </label>
        ))}
      </div>

      <div className="selectionSummary">
        <div className="summaryRow">
          <span className="label">Template</span>
          <span className="value">{templateId}</span>
        </div>

        {templateId === 1 ? (
          <>
            <div className="summaryRow">
              <span className="label">Selected Reviews</span>
              <span className="value">{selectedReviewIds.length}/3</span>
            </div>

            {chosenTitles.length > 0 && (
              <ul className="selectedReviewList">
                {chosenTitles.map((t, i) => (
                  <li key={`${t}-${i}`}>{t}</li>
                ))}
              </ul>
            )}
          </>
        ) : (
          <div className="summaryRow">
            <span className="label">ACTIVE Reviews</span>
            <span className="value">{activeIds.length} will be used</span>
          </div>
        )}
      </div>

      {error && <p className="errorText">{error}</p>}

      <div className="actionRow">
        <button className="btnGhost" onClick={() => nav("/community")} disabled={saving}>
          Cancel
        </button>

        {/* ✅ Journal(1)일 때만 모달로 선택 */}
        <button
          className="btnSecondary"
          onClick={() => setIsOpen(true)}
          disabled={saving || templateId !== 1}
        >
          Select Reviews
        </button>

        <button
          className="btnPrimary"
          onClick={handleCreate}
          // ✅ Journal(1)만 선택 3개 필요 / Map(2)은 바로 가능(단 activeIds>0)
          disabled={saving || (templateId === 1 && selectedReviewIds.length !== 3) || (templateId === 2 && activeIds.length === 0)}
        >
          {saving ? "Creating..." : "Create"}
        </button>
      </div>

      <CreateModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        stateReview={stateReview}
        reviewActions={reviewActions}
        templateId={templateId} // (모달 내부에서 1일 때만 사용)
        initialSelectedIds={selectedReviewIds}
        onConfirm={({ reviewIds }) => {
          setSelectedReviewIds(reviewIds);
          setIsOpen(false);
        }}
        saving={saving}
      />
    </div>
  );
}
