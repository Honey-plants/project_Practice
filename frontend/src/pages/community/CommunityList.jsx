import React, { useContext, useEffect } from "react";
import { Link } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";

export default function CommunityList() {
  const { stateCommunity, communityActions } = useContext(CommunityContext);

  useEffect(() => {
    communityActions.fetchList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Community</h2>
        <Link to="/community/new">New</Link>
      </div>

      {stateCommunity.error && <div className="errorBox">{stateCommunity.error}</div>}
      {stateCommunity.loading && <div>Loading...</div>}

      <ul>
        {stateCommunity.list.map((row) => {
          const id = row.id ?? row.community_id;
          const title = row.title ?? row.subject ?? "(no title)";
          return (
            <li key={id}>
              <Link to={`/community/${id}`}>{title}</Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}