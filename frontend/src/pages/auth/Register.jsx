import React, { useContext, useEffect, useMemo, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { MetaContext } from "../../context/MetaContext";
import { MemberAPI } from "../../api/memberApi";
import RestrictionsPicker from "../../components/restrictions/RestrictionsPicker";

/**
 * Register
 * - MetaContext(active 캐시) 기반으로 카테고리/아이템 노출
 * - RestrictionsPicker 공통 컴포넌트 사용
 * - 선택 item_ids 포함하여 회원가입 payload 전송
 */
export default function Register() {
  const nav = useNavigate();
  const { stateMeta, metaActions } = useContext(MetaContext);

  // ✅ active True 리스트만 (MetaContext가 active 캐시라고 가정 + 안전 필터는 Picker에서 onlyActive로 처리)
  const categories = useMemo(() => stateMeta?.restrictions || [], [stateMeta?.restrictions]);

  const [form, setForm] = useState({
    email: "",
    password: "",
    nickname: "",
    gender: "",
    country: "",
  });

  const [itemIds, setItemIds] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  // meta 비어있으면 1회 강제 refresh
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
    setItemIds((prev) => {
      const s = new Set(prev);
      if (s.has(id)) s.delete(id);
      else s.add(id);
      return Array.from(s);
    });
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    setMsg("");

    if (!form.email.trim() || !form.password.trim() || !form.nickname.trim()) {
      setMsg("이메일/비밀번호/닉네임은 필수입니다.");
      return;
    }

    setLoading(true);
    try {
      const payload = {
        email: form.email.trim(),
        password: form.password,
        nickname: form.nickname.trim(),
        gender: form.gender || null,
        country: form.country || null,
        item_ids: itemIds, // ✅ 선택된 ids
      };

      await MemberAPI.register(payload);
      setMsg("✅ 회원가입 완료! 로그인 페이지로 이동합니다.");
      nav("/login");
    } catch (err) {
      const detail =
        err?.response?.data?.detail ||
        err?.response?.data?.message ||
        err?.message ||
        "회원가입 실패";
      setMsg(`❌ ${detail}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="RegisterPage">
      <div className="RegisterHeader">
        <h2>회원가입</h2>
        <div className="RegisterLinks">
          <Link to="/login">로그인</Link>
        </div>
      </div>

      {msg && <div className={`RegisterMsg ${msg.startsWith("✅") ? "ok" : "err"}`}>{msg}</div>}

      <form className="card RegisterForm" onSubmit={onSubmit}>
        <div className="row">
          <label>이메일</label>
          <input
            name="email"
            value={form.email}
            onChange={onChange}
            placeholder="email@example.com"
            autoComplete="email"
          />
        </div>

        <div className="row">
          <label>비밀번호</label>
          <input
            name="password"
            value={form.password}
            onChange={onChange}
            type="password"
            placeholder="password"
            autoComplete="new-password"
          />
        </div>

        <div className="row">
          <label>닉네임</label>
          <input name="nickname" value={form.nickname} onChange={onChange} placeholder="nickname" />
        </div>

        <div className="row">
          <label>성별</label>
          <select name="gender" value={form.gender} onChange={onChange}>
            <option value="">선택안함</option>
            <option value="M">남</option>
            <option value="F">여</option>
          </select>
        </div>

        <div className="row">
          <label>국가</label>
          <input name="country" value={form.country} onChange={onChange} placeholder="Korea" />
        </div>

        <div className="RegisterDivider" />

        <div className="RegisterSectionTitle">
          <h3>알러지/제한 아이템 선택 (Active만)</h3>
          <div className="sub">
            선택된 아이템: <b>{itemIds.length}</b>개
          </div>
        </div>

        {stateMeta?.loading && <div className="infoBox">카테고리 불러오는 중...</div>}
        {stateMeta?.error && <div className="errorBox">{stateMeta.error}</div>}

        {!stateMeta?.loading && (categories || []).length === 0 && (
          <div className="infoBox">
            활성 카테고리/아이템이 없습니다.
            <button
              type="button"
              className="miniBtn"
              onClick={() => metaActions?.refresh?.({ force: true })}
              style={{ marginLeft: 8 }}
            >
              다시 불러오기
            </button>
          </div>
        )}

        {/* ✅ 공통 컴포넌트 사용 */}
        <RestrictionsPicker
          categories={categories}
          selectedIds={itemIds}
          onToggle={toggleItem}
          mode="select"
          onlyActive={true}
        />

        <div className="RegisterActions">
          <button type="submit" disabled={loading}>
            {loading ? "가입 중..." : "회원가입"}
          </button>
        </div>
      </form>
    </div>
  );
}
