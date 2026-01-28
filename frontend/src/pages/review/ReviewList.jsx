import React, { useContext, useEffect } from "react";
import { Link } from "react-router-dom";
import { ReviewContext } from "../../context/ReviewContext";

export default function ReviewList() {
  const { stateReview, reviewActions } = useContext(ReviewContext);

  useEffect(() => {
    reviewActions.fetchList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Review</h2>
        <Link to="/review/new">New</Link>
      </div>

      {stateReview.error && <div className="errorBox">{stateReview.error}</div>}
      {stateReview.loading && <div>Loading...</div>}

      <ul>
        {stateReview.list.map((row) => {
          const id = row.id ?? row.review_id;
          const title = row.title ?? row.subject ?? "(no title)";
          return (
            <li key={id}>
              <Link to={`/review/${id}`}>{title}</Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}