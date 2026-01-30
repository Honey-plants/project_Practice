import React from "react";
import RestrictionsAdminContainer from "../../components/restrictions/RestrictionsAdminContainer";
import "./Admin_new.css";

export default function Admin_new() {
  return (
    <div className="admin-container">
      <h2>관리자 카테고리 관리</h2>
      <RestrictionsAdminContainer />
    </div>
  );
}
