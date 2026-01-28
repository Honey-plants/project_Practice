import React, { useContext, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";

export default function CommunityEdit() {
  const { id } = useParams();
  const nav = useNavigate();
  const { stateCommunity, communityActions } = useContext(CommunityContext);

  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");

  useEffect(() => {
    (async () => {
      const d = await communityActions.fetchDetail(id);
      if (d) {
        setTitle(d.title ?? d.subject ?? "");
        setContent(d.content ?? d.body ?? "");
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onSave = async (e) => {
    e.preventDefault();
    await communityActions.update(id, { title, content });
    nav(`/community/${id}`);
  };

  return (
    <div style={{ padding: 16, maxWidth: 720 }}>
      <h2>Edit Community</h2>
      {stateCommunity.error && <div className="errorBox">{stateCommunity.error}</div>}

      <form onSubmit={onSave} style={{ display: "grid", gap: 10 }}>
        <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="title" />
        <textarea value={content} onChange={(e) => setContent(e.target.value)} placeholder="content" rows={8} />
        <button type="submit">Save</button>
      </form>
    </div>
  );
}