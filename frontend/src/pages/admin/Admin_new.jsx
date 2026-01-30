import React, { useEffect, useMemo, useState, useContext } from "react";
import "./Admin_new.css";
import { RestrictionsAdminAPI } from "../../api/restrictionsAdminApi";
import { MetaContext } from "../../context/MetaContext";

// ✅ 응답 형태가 [ ... ] 또는 { data:[...]} 둘 다 올 수 있으니 통합 파서
function unwrapRestrictions(payload) {
  if (Array.isArray(payload)) return payload;

  // { data: [...] }
  if (Array.isArray(payload?.data)) return payload.data;

  // 혹시 { categories:[...] } 형태면
  if (Array.isArray(payload?.categories)) return payload.categories;

  // 혹시 { data: { data: [...] } } 같은 2중 래핑이면
  if (Array.isArray(payload?.data?.data)) return payload.data.data;

  return [];
}

/**
 * Admin Restrictions Page
 * 1) active 상관없이 전체 조회
 * 2) 카테고리/아이템 인라인 수정 + active 토글
 * 3) 저장 후 meta(active 캐시) 갱신
 */
export default function AdminRestrictionsPage() {
  const { metaActions } = useContext(MetaContext);

  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [data, setData] = useState([]);

  const [q, setQ] = useState("");

  // ------------------ Load list (전체) ------------------
  const loadAll = async () => {
    setMsg("");
    setLoading(true);
    try {
      // ✅ Admin은 전체(활성/비활성) 조회
      const res = await RestrictionsAdminAPI.list({ onlyActive: false });

      // ✅ 여기서 핵심: 배열 / {data:배열} 둘 다 흡수
      const list = unwrapRestrictions(res.data);

      setData(list);
      setMsg(`✅ 조회 완료 (${list.length})`);
    } catch (e) {
      setMsg(`❌ ${e?.response?.data?.detail || e?.message || "조회 실패"}`);
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ------------------ Local update helpers ------------------
  const updateCategoryLocal = (category_id, patch) => {
    setData((prev) =>
      prev.map((c) => (c.category_id === category_id ? { ...c, ...patch } : c))
    );
  };

  const updateItemLocal = (category_id, item_id, patch) => {
    setData((prev) =>
      prev.map((c) => {
        if (c.category_id !== category_id) return c;
        return {
          ...c,
          items: (c.items || []).map((it) => (it.item_id === item_id ? { ...it, ...patch } : it)),
        };
      })
    );
  };

  // ------------------ Save to server ------------------
  const saveCategory = async (c) => {
    setMsg("");
    try {
      await RestrictionsAdminAPI.updateCategory(c.category_id, {
        category_label_ko: c.category_label_ko,
        category_label_en: c.category_label_en,
        category_active: !!c.category_active,
      });

      setMsg(`✅ 카테고리 저장 완료 (${c.category_id})`);

      // ✅ 사용자 화면(Register/Profile)은 active 캐시를 쓰므로 갱신
      await metaActions.refresh({ force: true });

      // ✅ Admin 화면은 전체를 보고 있으니 다시 전체 조회(동기화)
      await loadAll();
    } catch (e) {
      setMsg(`❌ ${e?.response?.data?.detail || e?.message || "카테고리 저장 실패"}`);
    }
  };

  const saveItem = async (category_id, it) => {
    setMsg("");
    try {
      await RestrictionsAdminAPI.updateItem(it.item_id, {
        item_label_ko: it.item_label_ko,
        item_label_en: it.item_label_en,
        item_active: !!it.item_active,
      });

      setMsg(`✅ 아이템 저장 완료 (${it.item_id})`);
      await metaActions.refresh({ force: true });
      await loadAll();
    } catch (e) {
      setMsg(`❌ ${e?.response?.data?.detail || e?.message || "아이템 저장 실패"}`);
    }
  };

  // ------------------ Search filter ------------------
  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    if (!needle) return data;

    const match = (s) => (s ?? "").toString().toLowerCase().includes(needle);

    return (data || [])
      .map((c) => {
        const catHit = match(c.category_label_ko) || match(c.category_label_en);
        if (catHit) return c;

        const items = (c.items || []).filter(
          (it) => match(it.item_label_ko) || match(it.item_label_en)
        );
        return { ...c, items };
      })
      .filter((c) => {
        const catHit = match(c.category_label_ko) || match(c.category_label_en);
        return catHit || (c.items || []).length > 0;
      });
  }, [data, q]);

  return (
    <div style={{ padding: 16, maxWidth: 1100, margin: "0 auto" }}>
      <h2>Admin Restrictions (전체)</h2>

      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
        <button onClick={loadAll} disabled={loading}>
          새로고침
        </button>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="검색 (카테고리/아이템)"
          style={{ flex: 1, padding: 8 }}
        />
      </div>

      {msg && <div style={{ marginBottom: 12 }}>{msg}</div>}

      {filtered.length === 0 ? (
        <div style={{ padding: 12, border: "1px solid #ddd" }}>
          표시할 데이터가 없습니다. (응답 파싱/권한/엔드포인트 확인)
        </div>
      ) : (
        filtered.map((c) => (
          <div key={c.category_id} className="card" style={{ marginBottom: 12, padding: 12 }}>
            <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
              <div style={{ minWidth: 70, fontWeight: 700 }}>Category</div>

              <input
                value={c.category_label_ko || ""}
                onChange={(e) =>
                  updateCategoryLocal(c.category_id, { category_label_ko: e.target.value })
                }
                placeholder="label_ko"
                style={{ padding: 8, minWidth: 220 }}
              />

              <input
                value={c.category_label_en || ""}
                onChange={(e) =>
                  updateCategoryLocal(c.category_id, { category_label_en: e.target.value })
                }
                placeholder="label_en"
                style={{ padding: 8, minWidth: 220 }}
              />

              <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
                <input
                  type="checkbox"
                  checked={!!c.category_active}
                  onChange={(e) =>
                    updateCategoryLocal(c.category_id, { category_active: e.target.checked })
                  }
                />
                active
              </label>

              <button onClick={() => saveCategory(c)}>저장</button>
            </div>

            <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 10 }}>
              {(c.items || []).map((it) => (
                <div
                  key={it.item_id}
                  style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}
                >
                  <div style={{ minWidth: 70, fontWeight: 700 }}>Item</div>

                  <input
                    value={it.item_label_ko || ""}
                    onChange={(e) =>
                      updateItemLocal(c.category_id, it.item_id, { item_label_ko: e.target.value })
                    }
                    placeholder="item_label_ko"
                    style={{ padding: 8, minWidth: 220 }}
                  />

                  <input
                    value={it.item_label_en || ""}
                    onChange={(e) =>
                      updateItemLocal(c.category_id, it.item_id, { item_label_en: e.target.value })
                    }
                    placeholder="item_label_en"
                    style={{ padding: 8, minWidth: 220 }}
                  />

                  <label style={{ display: "flex", gap: 6, alignItems: "center" }}>
                    <input
                      type="checkbox"
                      checked={!!it.item_active}
                      onChange={(e) =>
                        updateItemLocal(c.category_id, it.item_id, { item_active: e.target.checked })
                      }
                    />
                    active
                  </label>

                  <button onClick={() => saveItem(c.category_id, it)}>저장</button>
                </div>
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}