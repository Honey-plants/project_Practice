import React from "react";
import { Link, useLocation } from "react-router-dom";
import styles from "./BottomNav.module.css";

/* ─── SVG 아이콘 ─── */
const ReviewIcon = ({ active }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"
      stroke={active ? "#2E7D32" : "#999"}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"
      stroke={active ? "#2E7D32" : "#999"}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const HomeIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"
      stroke="#FFFFFF"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <polyline
      points="9,22 9,12 15,12 15,22"
      stroke="#FFFFFF"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const CommunityIcon = ({ active }) => (
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path
      d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"
      stroke={active ? "#2E7D32" : "#999"}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle
      cx="9"
      cy="7"
      r="4"
      stroke={active ? "#2E7D32" : "#999"}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M23 21v-2a4 4 0 0 0-3-3.87"
      stroke={active ? "#2E7D32" : "#999"}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M16 3.13a4 4 0 0 1 0 7.75"
      stroke={active ? "#2E7D32" : "#999"}
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

export default function BottomNav() {
  const location = useLocation();

  const isHome = location.pathname === "/";
  const isReview = location.pathname.startsWith("/review");
  const isCommunity = location.pathname.startsWith("/community");

  return (
    <nav className={styles.bottomNav}>
      {/* Review (왼쪽) */}
      <Link to="/review" className={`${styles.navItem} ${isReview ? styles.active : ""}`}>
        <ReviewIcon active={isReview} />
        <span>Review</span>
      </Link>

      {/* Home (가운데 — 큰 원형 버튼) */}
      <Link to="/" className={`${styles.navItem} ${styles.homeItem}`}>
        <div className={`${styles.homeCircle} ${isHome ? styles.homeCircleActive : ""}`}>
          <HomeIcon />
        </div>
      </Link>

      {/* Community (오른쪽) */}
      <Link to="/community" className={`${styles.navItem} ${isCommunity ? styles.active : ""}`}>
        <CommunityIcon active={isCommunity} />
        <span>Community</span>
      </Link>
    </nav>
  );
}
