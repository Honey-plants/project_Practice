import React, { useContext, useEffect } from "react";
import { Link } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";
import styles from "./CommunityList.module.css";

export default function CommunityList() {
  const { stateCommunity, communityActions } = useContext(CommunityContext);

  useEffect(() => {
    communityActions.fetchList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (stateCommunity.error) return <div className={styles.errorBox}>{stateCommunity.error}</div>;
  if (stateCommunity.loading) return <div className={styles.loading}>Loading...</div>;

  return (
    <div className={styles.listContainer}>
      <ul className={styles.list}>
        {stateCommunity.list.map((row) => {
          const id = row.id ?? row.community_id;
          const title = row.title ?? row.subject ?? "(no title)";
          return (
            <li key={id} className={styles.listItem}>
              <Link to={`/community/${id}`} className={styles.listLink}>{title}</Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}