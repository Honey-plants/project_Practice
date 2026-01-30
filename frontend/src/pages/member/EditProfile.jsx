import React, { useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MemberContext } from "../../context/MemberContext";
import { MetaContext } from "../../context/MetaContext";
import { MemberAPI } from "../../api/memberApi";
import RestrictionsPicker from "../../components/restrictions/RestrictionsPicker";

/**
 * EditProfile
 * - 내 기본 정보(nickname/gender/country) + item_ids(제한아이템) 수정
 * - 저장 시 "폼 전체" payload로 PATCH /member/me
 */
export default function EditProfile() {
  const nav = useNavigate();
  const { stateMember, memberActions } = useContext(MemberContext);
  const { stateMeta, metaActions } = useContext(MetaContext);

  const me = stateMember.me;

  // ✅ active True 리스트
  const categories = useMemo(() => stateMeta?.restrictions || [], [stateMeta?.restrictions]);

  // ------------------ form state ------------------
  const [form, setForm] = useState({
    nickname: "",
    gender: "",
    country: "",
    item_ids: [],
  });

  // me 로드되면 form 초기화
  useEffect(() => {
    if (!me) return;
    setForm({
      nickname: me.nickname || "",
      gender: me.gender || "",
      country: me.country || "",
      item_ids: Array.isArray(me.item_ids) ? me.item_ids : [],
    });
  }, [me]);

  // meta 비어있으면 1회 refresh
  useEffect(() => {
    if (!stateMeta?.loading && (categories || []).length === 0) {
      metaActions?.refresh?.({ force: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onChange = (e) => {
    const { name, value } = e.target;
    setForm((p) => ({ ...p, [name]: value }));
  };

  const toggleItem = (id) => {
    setForm((p) => {
      const s = new Set(p.item_ids || []);
      if (s.has(id)) s.delete(id);
      else s.add(id);
      return { ...p, item_ids: Array.from(s) };
    });
  };

  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  const onSave = async () => {
    setMsg("");
    setSaving(true);
    try {
      // ✅ "폼 전체" payload로 전송
      const payload = {
        nickname: form.nickname?.trim() || null,
        gender: form.gender || null,
        country: form.country || null,
        item_ids: form.item_ids || [],
      };

      await MemberAPI.updateMe(payload); // PATCH /member/me
      await memberActions.loadMe(); // me 갱신
      setMsg("✅ 저장 완료");
      nav("/member/profile");
    } catch (e) {
      setMsg(`❌ ${e?.response?.data?.detail || e?.message || "저장 실패"}`);
    } finally {
      setSaving(false);
    }
  };

  if (!me) return <div style={{ padding: 16 }}>Loading...</div>;

  return (
    <div style={{ padding: 16, maxWidth: 980, margin: "0 auto" }}>
      <h2>프로필 수정</h2>

      {msg && <div style={{ margin: "10px 0" }}>{msg}</div>}

      <div className="card" style={{ padding: 12, marginBottom: 12 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <div>
            <label style={{ display: "block", marginBottom: 6 }}>닉네임</label>
            <input
              name="nickname"
              value={form.nickname}
              onChange={onChange}
              style={{ padding: 10, border: "1px solid #ddd", borderRadius: 6, width: "100%" }}
            />
          </div>

          <div>
            <label style={{ display: "block", marginBottom: 6 }}>성별</label>
            <select
              name="gender"
              value={form.gender}
              onChange={onChange}
              style={{ padding: 10, border: "1px solid #ddd", borderRadius: 6, width: "100%" }}
            >
              <option value="">선택안함</option>
              <option value="M">남</option>
              <option value="F">여</option>
            </select>
          </div>

          <div>
            <label style={{ display: "block", marginBottom: 6 }}>국가</label>
            <input
              name="country"
              value={form.country}
              onChange={onChange}
              style={{ padding: 10, border: "1px solid #ddd", borderRadius: 6, width: "100%" }}
            />
          </div>
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline" }}>
        <h3>제한 아이템 수정 (Active만)</h3>
        <div>
          선택: <b>{(form.item_ids || []).length}</b>개
        </div>
      </div>

      {stateMeta?.loading && <div style={{ margin: "10px 0" }}>카테고리 불러오는 중...</div>}
      {stateMeta?.error && <div className="errorBox">{stateMeta.error}</div>}

      {/* ✅ 공통 컴포넌트 사용 */}
      <RestrictionsPicker
        categories={categories}
        selectedIds={form.item_ids}
        onToggle={toggleItem}
        mode="select"
        onlyActive={true}
      />

      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 12 }}>
        <button onClick={onSave} disabled={saving}>
          {saving ? "저장 중..." : "저장"}
        </button>
      </div>
    </div>
  );
}