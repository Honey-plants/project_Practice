import React, { useContext, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MemberContext } from "../../context/MemberContext";

export default function EditProfile() {
  const { stateMember, memberActions } = useContext(MemberContext);
  const nav = useNavigate();

  const [nickname, setNickname] = useState("");
  const [country, setCountry] = useState("");
  const [gender, setGender] = useState("");

  useEffect(() => {
    if (stateMember.me) {
      setNickname(stateMember.me.nickname || "");
      setCountry(stateMember.me.country || "");
      setGender(stateMember.me.gender || "");
    }
  }, [stateMember.me]);

  const onSave = async (e) => {
    e.preventDefault();
    await memberActions.updateMe({ nickname, country, gender });
    nav("/member/profile");
  };

  return (
    <div style={{ padding: 16, maxWidth: 520 }}>
      <h2>Edit Profile</h2>

      <form onSubmit={onSave} style={{ display: "grid", gap: 10 }}>
        <input value={nickname} onChange={(e) => setNickname(e.target.value)} placeholder="nickname" />
        <input value={country} onChange={(e) => setCountry(e.target.value)} placeholder="country" />
        <input value={gender} onChange={(e) => setGender(e.target.value)} placeholder="gender" />
        <button type="submit">Save</button>
      </form>

      {stateMember.error && <div className="errorBox">{stateMember.error}</div>}
    </div>
  );
}