import React, { useContext, useEffect, useMemo } from "react";
import { Link } from "react-router-dom";
import { MemberContext } from "../../context/MemberContext";
import { MetaContext } from "../../context/MetaContext";
import RestrictionsPicker from "../../components/restrictions/RestrictionsPicker";

/**
 * Profile
 * 1) 본인 정보 노출
 * 2) 본인이 선택한 item_ids만 "읽기 전용"으로 표시
 * 3) Edit 클릭 시 /member/edit 로 이동하여 수정
 */
export default function Profile() {
  const { stateMember, memberActions } = useContext(MemberContext);
  const { stateMeta, metaActions } = useContext(MetaContext);

  const me = stateMember.me;

  // ✅ 내가 선택한 item_ids만
  const selectedIds = useMemo(() => (me?.item_ids ? me.item_ids : []), [me]);

  // ✅ active True 카테고리/아이템(공용 meta 캐시)
  const categories = useMemo(() => stateMeta?.restrictions || [], [stateMeta?.restrictions]);

  // ✅ 새로고침 직후 meta가 비어있으면 1회 로드 (active만)
  useEffect(() => {
    if (!stateMeta?.loading && (categories || []).length === 0) {
      metaActions?.refresh?.({ force: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ✅ 새로고침 직후 me가 없으면 로드
  useEffect(() => {
    if (!me && !stateMember?.loading) {
      memberActions?.loadMe?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div style={{ padding: 16, maxWidth: 980, margin: "0 auto" }}>

      {stateMember?.error && (
        <div style={{ margin: "10px 0", padding: 10, border: "1px solid #ffbcbc", background: "#ffecec" }}>
          {stateMember.error}
        </div>
      )}

      {!me ? (
        <div style={{ padding: "12px 0" }}>Loading me...</div>
      ) : (
        <div className="card" style={{ padding: 12, marginBottom: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "120px 1fr", rowGap: 8 }}>
            <div style={{ fontWeight: 700 }}>Email</div>
            <div>{me.email}</div>

            <div style={{ fontWeight: 700 }}>Nickname</div>
            <div>{me.nickname}</div>

            <div style={{ fontWeight: 700 }}>Gender</div>
            <div>{me.gender || "-"}</div>

            <div style={{ fontWeight: 700 }}>Country</div>
            <div>{me.country || "-"}</div>

            <div style={{ fontWeight: 700 }}>Selected</div>
            <div>{selectedIds.length}개</div>
          </div>
        </div>
      )}

      <h3 style={{ marginTop: 18 }}>내가 선택한 제한 아이템 (읽기 전용 / Active만)</h3>

      {stateMeta?.loading && <div style={{ margin: "10px 0" }}>카테고리 불러오는 중...</div>}
      {stateMeta?.error && (
        <div style={{ margin: "10px 0", padding: 10, border: "1px solid #ffbcbc", background: "#ffecec" }}>
          {stateMeta.error}
        </div>
      )}

      {/* ✅ 선택된 것만 보여주기 */}
      <RestrictionsPicker
        categories={categories}
        selectedIds={selectedIds}
        mode="view"       // ✅ 읽기 전용(선택된 것만)
        onlyActive={true} // ✅ active True만
      />

      <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end" }}>
        <Link to="/member/edit" style={{ padding: "10px 14px", borderRadius: 6, border: "1px solid #333", background: "#333", color: "#fff", textDecoration: "none" }}>
          Edit
        </Link>
      </div>
    </div>
  );
}
