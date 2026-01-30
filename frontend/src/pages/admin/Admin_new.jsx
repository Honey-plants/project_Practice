import React from "react";
import RestrictionsAdminContainer from "../../components/restrictions/RestrictionsAdminContainer";
import "./Admin_new.css";

export default function Admin_new() {
  return (
    <div className="admin-container">
      <h2>Admin Restrictions</h2>
      <RestrictionsAdminContainer />
    </div>
  );
}
