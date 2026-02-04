import React, { useContext, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";
import { ReviewContext } from "../../context/ReviewContext";
import CreateModal from "../../components/community/CreateModal";
import "../../styles/CommunityCreate.css";

const TEMPLATES = [
  { id: 1, img: "/map_temp.png", title: "Template 1 · Map", desc: "Use all active reviews to generate a travel map" },
  { id: 2, img: "/debug_out.png", title: "Template 2 · Journal", desc: "Pick 3 reviews and create a funny travel journal" },
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

  const chosenTitles = useMemo(() => {
    const list = stateReview.list ?? [];
    const map = new Map(list.map((r) => [r.review_id ?? r.id, r]));
    return selectedReviewIds
      .map((id) => map.get(id))
      .filter(Boolean)
      .map((r) => r.review_title ?? r.title ?? "(no title)");
  }, [stateReview.list, selectedReviewIds]);

  const allReviewIds = useMemo(
    () => (stateReview.list ?? []).map(r => r.review_id ?? r.id),
    [stateReview.list]
  );

  const handleCreate = async () => {
    setSaving(true); setError("");
    try {
      if (templateId === 2 && selectedReviewIds.length !== 3) {
        setError("Template 2 requires exactly 3 active reviews.");
        return;
      }
    await communityActions.create({
      template_id: templateId,
      review_ids: templateId === 1 ? allReviewIds : selectedReviewIds,
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
          <label key={t.id} className={`templateCard ${templateId === t.id ? "active" : ""}`} role="radio" aria-checked={templateId === t.id}>
            <input
              type="radio"
              name="template"
              checked={templateId === t.id}
              onChange={() => { setTemplateId(t.id); setSelectedReviewIds([]); }}
            />
            <img src={t.img} alt={t.title} />
            <div className="info"><div className="title">{t.title}</div><div className="desc">{t.desc}</div></div>
          </label>
        ))}
      </div>

      <div className="selectionSummary">
        <div className="summaryRow"><span className="label">Template</span><span className="value">{templateId}</span></div>

        {templateId === 2 ? (
          <>
            <div className="summaryRow"><span className="label">Selected Reviews</span><span className="value">{selectedReviewIds.length}/3</span></div>
            {chosenTitles.length > 0 && (
              <ul className="selectedReviewList">
                {chosenTitles.map((t, i) => <li key={`${t}-${i}`}>{t}</li>)}
              </ul>
            )}
          </>
        ) : (
          <div className="summaryRow"><span className="value">Reviews will be selected automatically</span></div>
        )}
      </div>

      {error && <p className="errorText">{error}</p>}

      <div className="actionRow">
        <button className="btnGhost" onClick={() => nav("/community")} disabled={saving}>Cancel</button>

        <button
          className="btnSecondary"
          onClick={() => setIsOpen(true)}
          disabled={saving || templateId !== 2}
        >
          Select Reviews
        </button>

        <button
          className="btnPrimary"
          onClick={handleCreate}
          disabled={saving || (templateId === 2 && selectedReviewIds.length !== 3)}
        >
          {saving ? "Creating..." : "Create"}
        </button>
      </div>

      <CreateModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        stateReview={stateReview}
        reviewActions={reviewActions}
        templateId={templateId}
        initialSelectedIds={selectedReviewIds}
        onConfirm={({ reviewIds }) => { setSelectedReviewIds(reviewIds); setIsOpen(false); }}
        saving={saving}
      />
    </div>
  );
}
