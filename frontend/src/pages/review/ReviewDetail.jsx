import React, { useContext, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";

export default function ReviewDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { stateReview, reviewActions } = useContext(ReviewContext);

  useEffect(() => {
    reviewActions.fetchDetail(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onDelete = async () => {
    await reviewActions.remove(id);
    nav("/review");
  };

  const d = stateReview.detail;

  return (
    <div style={{ padding: 16, maxWidth: 720 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Review Detail</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <Link to={`/review/${id}/edit`}>Edit</Link>
          <button onClick={onDelete}>Delete</button>
        </div>
      </div>

      {stateReview.error && <div className="errorBox">{stateReview.error}</div>}
      {!d ? <div>Loading...</div> : <pre className="card">{JSON.stringify(d, null, 2)}</pre>}
    </div>
  );
}