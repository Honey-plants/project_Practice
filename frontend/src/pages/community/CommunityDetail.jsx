import React, { useContext, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";
import styles from "./CommunityDetail.module.css";

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
    <div className={styles.container}>
      <div className={styles.header}>
        <h2>Community Detail</h2>
        <div className={styles.actions}>
          <Link to={`/community/${id}/edit`} className={styles.editLink}>Edit</Link>
          <button onClick={onDelete} className={styles.deleteButton}>Delete</button>
        </div>
      </div>

      {stateCommunity.error && <div className={styles.errorBox}>{stateCommunity.error}</div>}
      {!d ? <div className={styles.loading}>Loading...</div> : <pre className={styles.content}>{JSON.stringify(d, null, 2)}</pre>}
    </div>
  );
}