import React, { useEffect, useState } from "react";
import { MemberAPI } from "../../api/memberApi";
import { useNavigate, Link } from "react-router-dom";

export default function Register() {
  const nav = useNavigate();

  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");
  const [nickname, setNickname] = useState("");
  const [gender, setGender] = useState("");
  const [country, setCountry] = useState("");

  const [categories, setCategories] = useState([]);
  const [selectedItemIds, setSelectedItemIds] = useState(new Set());
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const r = await MemberAPI.getCategoriesWithItems();
        // 기대 형태: [{category_id, category_label_ko, items:[{item_id, item_label_ko}]}]
        setCategories(Array.isArray(r.data) ? r.data : r.data?.items ?? []);
      } catch (e) {
        setError(e.message || "카테고리/아이템 조회 실패");
      }
    })();
  }, []);

  const toggleItem = (itemId) => {
    setSelectedItemIds((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) next.delete(itemId);
      else next.add(itemId);
      return next;
    });
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");

    try {
      await MemberAPI.register({
        email,
        password: pw,
        nickname,
        gender: gender || null,
        country: country || null,
        item_ids: Array.from(selectedItemIds),
      });

      nav("/login");
    } catch (e2) {
      setError(e2.message || "회원가입 실패");
    }
  };

  return (
    <div style={{ padding: 16, maxWidth: 900 }}>
      <h2>Register</h2>

      <form onSubmit={onSubmit} style={{ display: "grid", gap: 10, maxWidth: 420 }}>
        <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
        <input value={pw} onChange={(e) => setPw(e.target.value)} placeholder="password" type="password" />
        <input value={nickname} onChange={(e) => setNickname(e.target.value)} placeholder="nickname" />
        <input value={gender} onChange={(e) => setGender(e.target.value)} placeholder="gender(optional)" />
        <input value={country} onChange={(e) => setCountry(e.target.value)} placeholder="country(optional)" />
        <button type="submit">Create Account</button>
        <div>
          <Link to="/login">Go Login</Link>
        </div>
      </form>

      <hr style={{ margin: "16px 0" }} />

      <h3>Category / Item 선택</h3>
      {error && <div className="errorBox">{error}</div>}

      {categories.map((c) => (
        <div key={c.category_id ?? c.id} className="card">
          <div style={{ fontWeight: 700, marginBottom: 8 }}>
            {c.category_label_ko ?? c.category_label_en ?? c.label ?? "Category"}
          </div>

          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {(c.items || []).map((it) => {
              const itemId = it.item_id ?? it.id;
              const label = it.item_label_ko ?? it.item_label_en ?? it.label ?? `item#${itemId}`;
              const checked = selectedItemIds.has(itemId);

              return (
                <label key={itemId} style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleItem(itemId)}
                  />
                  {label}
                </label>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}