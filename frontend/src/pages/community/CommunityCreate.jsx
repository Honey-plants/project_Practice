import React, { useContext, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";
import { ReviewContext } from "../../context/ReviewContext";
import CreateModal from "../../components/community/CreateModal";
import "../../styles/CommunityCreate.css";

const TEMPLATES = [
  { id: 1, img: "/template_journal.png", title: "Template 1 · Journal", desc: "Pick 3 reviews and create a funny travel journal" },
  { id: 2, img: "/template_map.png", title: "Template 2 · Map", desc: "Use all active reviews to generate a travel map" },
];

export default function CommunityCreate() {
  const nav = useNavigate();
  const { communityActions } = useContext(CommunityContext);
  const { stateReview, reviewActions } = useContext(ReviewContext);

  const [templateId, setTemplateId] = useState(1);
  const [isOpen, setIsOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const handleConfirm = async ({ reviewIds }) => {
    setSaving(true); setError("");
    try {
      await communityActions.create({ template_id: templateId, review_ids: reviewIds });
      setIsOpen(false); nav("/community");
    } catch (e) {
      setError(e?.message || "Generate AI image failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ padding: 16, maxWidth: 720 }}>
      <h2>New Community Post</h2>

      <div className="templateGrid">
        {TEMPLATES.map((t) => (
          <label key={t.id} className={`templateCard ${templateId === t.id ? "active" : ""}`} role="radio" aria-checked={templateId === t.id}>
            <input type="radio" name="template" checked={templateId === t.id} onChange={() => setTemplateId(t.id)} />
            <img src={t.img} alt={t.title} />
            <div className="info"><div className="title">{t.title}</div><div className="desc">{t.desc}</div></div>
          </label>
        ))}
      </div>

      {error && <p style={{ color: "crimson" }}>{error}</p>}

      <button type="button" onClick={() => setIsOpen(true)} disabled={saving} style={{ marginTop: 16 }}>
        Select Reviews
      </button>

      <CreateModal
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
        stateReview={stateReview}
        reviewActions={reviewActions}
        templateId={templateId}
        onConfirm={handleConfirm}
        saving={saving}
      />
    </div>
  );
}
