import React, { useContext, useEffect } from "react";
import { Link } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";

export default function CommunityList() {
  const { stateCommunity, communityActions } = useContext(CommunityContext);

  useEffect(() => {
    communityActions.fetchList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (stateCommunity.error) return <div className="errorBox">{stateCommunity.error}</div>;
  if (stateCommunity.loading) return <div>Loading...</div>;

  return (
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
  );
}