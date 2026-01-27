import React, { useContext } from "react";
import { Link } from "react-router-dom";
import { MemberContext } from "../../context/MemberContext";

export default function Profile() {
  const { stateMember, memberActions } = useContext(MemberContext);

  return (
    <div style={{ padding: 16, maxWidth: 720 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Profile</h2>
        <div style={{ display: "flex", gap: 8 }}>
          <button onClick={memberActions.loadMe}>Reload</button>
          <Link to="/member/edit">Edit</Link>
        </div>
      </div>

      {stateMember.error && <div className="errorBox">{stateMember.error}</div>}

      {!stateMember.me ? (
        <div style={{ padding: "12px 0" }}>Loading me...</div>
      ) : (
        <pre className="card">{JSON.stringify(stateMember.me, null, 2)}</pre>
      )}
    </div>
  );
}