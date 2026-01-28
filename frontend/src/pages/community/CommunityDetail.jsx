import React, { useContext, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";

export default function CommunityDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { stateCommunity, communityActions } = useContext(CommunityContext);

  useEffect(() => {
    communityActions.fetchDetail(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onDelete = async () => {
    await communityActions.remove(id);
    nav("/community");
  };

  const d = stateCommunity.detail;

  return (
    <div style={{ padding: 16, maxWidth: 720 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Community Detail</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <Link to={`/community/${id}/edit`}>Edit</Link>
          <button onClick={onDelete}>Delete</button>
        </div>
      </div>

      {stateCommunity.error && <div className="errorBox">{stateCommunity.error}</div>}
      {!d ? <div>Loading...</div> : <pre className="card">{JSON.stringify(d, null, 2)}</pre>}
    </div>
  );
}