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
          const title = row.title ?? row.subject ?? `Community #${id}`;
          const img = row.image_urls?.[0]; // ✅ 첫 이미지 썸네일
          const member = row.member_id;
          const recommend = row.recommend;

          return (
            <li key={id} className={styles.listItem}>
              <Link to={`/community/${id}`} className={styles.listLink}>
                <p>{member} (nickname)</p>
                {img ? (
                  <img
                    src={img}
                    className={styles.thumb}
                    loading="lazy"
                    onError={(e) => {
                      e.currentTarget.style.display = "none"; // 깨진 이미지 숨김
                    }}
                  />
                ) : (
                  <div className={styles.thumbPlaceholder}>No Image</div>
                )}
                
                <div className={styles.meta}>

                  <p>{recommend}</p>
                  {/* 필요하면 날짜/추천도 표시 가능 */}
                  {/* <div className={styles.sub}>{row.created_at}</div> */}
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
