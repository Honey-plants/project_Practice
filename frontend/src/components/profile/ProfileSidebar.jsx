import React from "react";
import { Link } from "react-router-dom";
import styles from "./ProfileSidebar.module.css";

/**
 * ProfileSidebar
 * 프로필 왼쪽 사이드바 컴포넌트
 */
export default function ProfileSidebar({ member }) {
  if (!member) {
    return (
      <div className={styles.loading}>
        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className={styles.sidebar}>
      <div className={styles.profileSection}>
        <div className={styles.avatar}>
          {member.nickname?.charAt(0).toUpperCase() || "U"}
        </div>
        <h2 className={styles.nickname}>
          {member.nickname || "사용자"}
        </h2>
        <p className={styles.email}>
          {member.email}
        </p>
      </div>

      <div className={styles.infoSection}>
        <div className={styles.infoItem}>
          <p className={styles.infoLabel}>Country</p>
          <p className={styles.infoValue}>
            {member.country || "미설정"}
          </p>
        </div>
        <div className={styles.infoItem}>
          <p className={styles.infoLabel}>Gender</p>
          <p className={styles.infoValue}>
            {member.gender || "미설정"}
          </p>
        </div>
      </div>

      <div className={styles.actions}>
        <Link to="/member/edit" className={styles.editButton}>
          Information Edit
        </Link>
      </div>
    </div>
  );
}
