import React, { useEffect, useMemo, useState } from "react";
import './Admin_new.css';
/**
 * Admin Restrictions Page
 * - 초기 진입 시 전체 카테고리/아이템 조회
 * - 일괄 등록(배치)
 * - 카테고리/아이템 인라인 수정
 * - category_active / item_active 토글
 */
export default function AdminRestrictionsPage() {
  // ------------------ API ------------------
  const BASE = "http://127.0.0.1:8004";
  const API = {
    list: `${BASE}/admin/restrictions`,                 // GET
    batchCreate: `${BASE}/admin/restrictions/batch`,    // POST
    updateCategory: (id) => `${BASE}/admin/restrictions/category/${id}`, // PUT
    updateItem: (id) => `${BASE}/admin/restrictions/item/${id}`,         // PUT
  };

  // ------------------ State ------------------
  const [accessToken, setAccessToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");
  const [data, setData] = useState([]); // [{category_id, category_label_ko, category_label_en, category_active, items:[...]}]

  // 검색/필터
  const [q, setQ] = useState("");
  const [onlyActive, setOnlyActive] = useState(false);

  // 배치 등록 폼
  const emptyItem = () => ({
    item_label_ko: "",
    item_label_en: "",
    item_active: true,
  });
  const emptyCategory = () => ({
    category_label_ko: "",
    category_label_en: "",
    category_active: true,
    items: [emptyItem()],
  });

  const [draftCategories, setDraftCategories] = useState([emptyCategory()]);
  const [savingBatch, setSavingBatch] = useState(false);

  // ------------------ Helpers ------------------
  const authHeaders = useMemo(() => {
    return {
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    };
  }, [accessToken]);

  const parseResponse = async (res) => {
    const raw = await res.text();
    let json = null;
    try {
      json = raw ? JSON.parse(raw) : null;
    } catch {
      json = null;
    }
    return { raw, json };
  };

  const showError = (res, raw, json) => {
    const detail = json?.detail ?? json?.message ?? raw ?? `요청 실패(status ${res.status})`;
    const msg = typeof detail === "string" ? detail : JSON.stringify(detail, null, 2);
    throw new Error(msg);
  };

  // ------------------ Load list ------------------
  const loadAll = async () => {
    setMsg("");
    setLoading(true);
    try {
      const res = await fetch(API.list, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
      });

      const { raw, json } = await parseResponse(res);
      if (!res.ok) showError(res, raw, json);

      // 서버가 {categories:[...]} 로 줄 수도 있고, 그냥 [...]로 줄 수도 있으니 흡수
      const list = Array.isArray(json) ? json : (json?.categories ?? json?.data ?? []);
      setData(list);
      setMsg("✅ 조회 완료");
    } catch (e) {
      setMsg(`❌ ${e?.message || "조회 실패"}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // 초기 진입 시 자동 조회
    loadAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ------------------ Filtered view ------------------
  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const match = (s) => (s ?? "").toString().toLowerCase().includes(needle);

    return (data || []).filter((c) => {
      if (onlyActive && !c.category_active) return false;

      const catHit =
        !needle ||
        match(c.category_label_ko) ||
        match(c.category_label_en);

      const items = (c.items || []).filter((it) => {
        if (onlyActive && !it.item_active) return false;
        if (!needle) return true;
        return match(it.item_label_ko) || match(it.item_label_en);
      });

      // 검색 중이면: 카테고리 hit 이거나 아이템 중 hit이 1개라도 있으면 보여줌
      if (!needle) return true;
      return catHit || items.length > 0;
    }).map((c) => {
      // onlyActive면 items도 필터된 것만 렌더링
      const items = (c.items || []).filter((it) => (onlyActive ? !!it.item_active : true));
      return { ...c, items };
    });
  }, [data, q, onlyActive]);

  // ------------------ Inline edit: category/item ------------------
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

  const saveCategory = async (c) => {
    setMsg("");
    try {
      const payload = {
        category_label_ko: c.category_label_ko,
        category_label_en: c.category_label_en,
        category_active: !!c.category_active,
      };

      const res = await fetch(API.updateCategory(c.category_id), {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify(payload),
      });

      const { raw, json } = await parseResponse(res);
      if (!res.ok) showError(res, raw, json);

      setMsg(`✅ 카테고리 ${c.category_id} 저장 완료`);
      // 필요하면 json 응답으로 동기화
    } catch (e) {
      setMsg(`❌ ${e?.message || "카테고리 저장 실패"}`);
    }
  };

  const saveItem = async (category_id, it) => {
    setMsg("");
    try {
      const payload = {
        item_label_ko: it.item_label_ko,
        item_label_en: it.item_label_en,
        item_active: !!it.item_active,
      };

      const res = await fetch(API.updateItem(it.item_id), {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify(payload),
      });

      const { raw, json } = await parseResponse(res);
      if (!res.ok) showError(res, raw, json);

      setMsg(`✅ 아이템 ${it.item_id} 저장 완료`);
    } catch (e) {
      setMsg(`❌ ${e?.message || "아이템 저장 실패"}`);
    }
  };

  // ------------------ Batch create (등록) ------------------
  const addDraftCategory = () => setDraftCategories((p) => [...p, emptyCategory()]);
  const removeDraftCategory = (idx) =>
    setDraftCategories((p) => (p.length <= 1 ? p : p.filter((_, i) => i !== idx)));

  const addDraftItem = (catIdx) =>
    setDraftCategories((p) =>
      p.map((c, i) => (i === catIdx ? { ...c, items: [...(c.items || []), emptyItem()] } : c))
    );

  const removeDraftItem = (catIdx, itemIdx) =>
    setDraftCategories((p) =>
      p.map((c, i) => {
        if (i !== catIdx) return c;
        if ((c.items || []).length <= 1) return c;
        return { ...c, items: c.items.filter((_, j) => j !== itemIdx) };
      })
    );

  const updateDraftCategoryField = (catIdx, field, value) =>
    setDraftCategories((p) => p.map((c, i) => (i === catIdx ? { ...c, [field]: value } : c)));

  const updateDraftItemField = (catIdx, itemIdx, field, value) =>
    setDraftCategories((p) =>
      p.map((c, i) => {
        if (i !== catIdx) return c;
        const items = (c.items || []).map((it, j) => (j === itemIdx ? { ...it, [field]: value } : it));
        return { ...c, items };
      })
    );

  const buildBatchPayload = () => {
    const normalized = draftCategories
      .map((c) => {
        const items = (c.items || [])
          .map((it) => ({
            item_label_ko: (it.item_label_ko || "").trim(),
            item_label_en: (it.item_label_en || "").trim(),
            item_active: it.item_active !== false, // default true
          }))
          .filter((it) => it.item_label_ko && it.item_label_en);

        return {
          category_label_ko: (c.category_label_ko || "").trim(),
          category_label_en: (c.category_label_en || "").trim(),
          category_active: c.category_active !== false, // default true
          items,
        };
      })
      .filter((c) => c.category_label_ko && c.category_label_en);

    return { categories: normalized };
  };

  const submitBatch = async () => {
    setMsg("");
    setSavingBatch(true);
    try {
      const payload = buildBatchPayload();
      if (!payload.categories.length) throw new Error("등록할 카테고리가 없습니다.");

      // 간단 검증: items가 비어있으면 허용할지 정책에 따라
      // 여기서는 빈 items도 허용(카테고리만 만들기)하도록 둠.

      const res = await fetch(API.batchCreate, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify(payload),
      });

      const { raw, json } = await parseResponse(res);
      if (!res.ok) showError(res, raw, json);

      setMsg("✅ 등록 완료! 목록 새로고침 중...");
      setDraftCategories([emptyCategory()]);
      await loadAll();
    } catch (e) {
      setMsg(`❌ ${e?.message || "등록 실패"}`);
    } finally {
      setSavingBatch(false);
    }
  };

  // ------------------ UI ------------------
  return (
    <div className="container-admin">
      <section className="section-top">
        <div className="toolbar">
          <h1 className="admin-title">Admin Restrictions</h1>
          <button onClick={loadAll}>
            {loading ? "불러오는 중..." : "새로고침"}
          </button>
        </div>

        <div className="panel">
          <div className="toolbar">
            <h3>Access Token (Admin)</h3>
            <input
              type="search"
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              placeholder="Bearer 빼고 토큰만 입력"
            />
          </div>
          <p className="hint">
            * admin API가 보호돼 있으면 토큰 필수
          </p>
        </div>

        <div className="panel">
          <div className="toolbar">
            <h3>검색</h3>
            <input
              type="search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="검색: ko/en"
            />
            <label className="checkbox">
              <input
                type="checkbox"
                checked={onlyActive}
                onChange={(e) => setOnlyActive(e.target.checked)}
              />
              active만
            </label>
          </div>
        </div>

        <div className="panel">
          <p className="notice">{msg}</p>
        </div>
      </section>

      <main>
        <section className="section-left">
          <div className="toolbar">
            <h3>목록 (조회 / 수정)</h3>
          </div>

          <ul>
            {filtered.map((c) => (
              <li key={c.category_id} className="categorybox">
                <ul className="row">
                  <li>
                    <span>category_active</span>
                    <input
                      type="checkbox"
                      checked={c.category_active}
                      onChange={(e) =>
                        updateCategoryLocal(c.category_id, {
                          category_active: e.target.checked,
                        })
                      }
                    />
                  </li>
                  <li>
                    <span>category_id</span>
                    <span>{c.category_id}</span>
                  </li>
                  <li>
                    <span>category_label_ko</span>
                    <input
                      value={c.category_label_ko}
                      onChange={(e) =>
                        updateCategoryLocal(c.category_id, {
                          category_label_ko: e.target.value,
                        })
                      }
                    />
                  </li>
                  <li>
                    <span>category_label_en</span>
                    <input
                      value={c.category_label_en}
                      onChange={(e) =>
                        updateCategoryLocal(c.category_id, {
                          category_label_en: e.target.value,
                        })
                      }
                    />
                  </li>
                  <li>
                    <button onClick={() => saveCategory(c)}>
                      카테고리 저장
                    </button>
                  </li>
                </ul>

                <ul>
                  <li className="itembox">
                    {c.items.map((it) => (
                      <ul key={it.item_id} className="row">
                        <li>
                          <input
                            type="checkbox"
                            checked={it.item_active}
                            onChange={(e) =>
                              updateItemLocal(
                                c.category_id,
                                it.item_id,
                                { item_active: e.target.checked }
                              )
                            }
                          />
                        </li>
                        <li>{it.item_id}</li>
                        <li>
                          <input
                            value={it.item_label_ko}
                            onChange={(e) =>
                              updateItemLocal(
                                c.category_id,
                                it.item_id,
                                { item_label_ko: e.target.value }
                              )
                            }
                          />
                        </li>
                        <li>
                          <input
                            value={it.item_label_en}
                            onChange={(e) =>
                              updateItemLocal(
                                c.category_id,
                                it.item_id,
                                { item_label_en: e.target.value }
                              )
                            }
                          />
                        </li>
                        <li>
                          <button onClick={() => saveItem(it)}>
                            아이템 저장
                          </button>
                        </li>
                      </ul>
                    ))}
                  </li>
                </ul>
              </li>
            ))}
          </ul>
        </section>
        <section className="section-right">
          <div className="toolbar">
            <h3>등록 (일괄 등록)</h3>
            <button onClick={addDraftCategory}>+ 카테고리 추가</button>
          </div>

          <ul>
            {draftCategories.map((c, catIdx) => (
              <li key={catIdx} className="categorybox">
                <ul className="row">
                  <li>
                    <span>category_active</span>
                    <input
                      type="checkbox"
                      checked={c.category_active !== false}
                      onChange={(e) =>
                        updateDraftCategoryField(
                          catIdx,
                          "category_active",
                          e.target.checked
                        )
                      }
                    />
                  </li>
                  <li>
                    <span>NEW</span>
                  </li>
                  <li>
                    <span>category_label_ko</span>
                    <input
                      value={c.category_label_ko}
                      onChange={(e) =>
                        updateDraftCategoryField(
                          catIdx,
                          "category_label_ko",
                          e.target.value
                        )
                      }
                    />
                  </li>
                  <li>
                    <span>category_label_en</span>
                    <input
                      value={c.category_label_en}
                      onChange={(e) =>
                        updateDraftCategoryField(
                          catIdx,
                          "category_label_en",
                          e.target.value
                        )
                      }
                    />
                  </li>
                  <li>
                    <button
                      onClick={() => removeDraftCategory(catIdx)}
                      disabled={draftCategories.length <= 1}
                    >
                      삭제
                    </button>
                  </li>
                </ul>

                <ul>
                  <li className="itembox">
                    <ul className="row row-label">
                      <li>item_active</li>
                      <li>NEW</li>
                      <li>item_label_ko</li>
                      <li>item_label_en</li>
                      <li>
                        <button onClick={() => addDraftItem(catIdx)}>
                          + 아이템 추가
                        </button>
                      </li>
                    </ul>

                    {(c.items || []).map((it, itemIdx) => (
                      <ul key={itemIdx} className="row">
                        <li>
                          <input
                            type="checkbox"
                            checked={it.item_active !== false}
                            onChange={(e) =>
                              updateDraftItemField(
                                catIdx,
                                itemIdx,
                                "item_active",
                                e.target.checked
                              )
                            }
                          />
                        </li>
                        <li>NEW</li>
                        <li>
                          <input
                            value={it.item_label_ko}
                            onChange={(e) =>
                              updateDraftItemField(
                                catIdx,
                                itemIdx,
                                "item_label_ko",
                                e.target.value
                              )
                            }
                          />
                        </li>
                        <li>
                          <input
                            value={it.item_label_en}
                            onChange={(e) =>
                              updateDraftItemField(
                                catIdx,
                                itemIdx,
                                "item_label_en",
                                e.target.value
                              )
                            }
                          />
                        </li>
                        <li>
                          <button
                            onClick={() =>
                              removeDraftItem(catIdx, itemIdx)
                            }
                            disabled={c.items.length <= 1}
                          >
                            삭제
                          </button>
                        </li>
                      </ul>
                    ))}
                  </li>
                </ul>
              </li>
            ))}
          </ul>

          <div className="toolbar">
            <button onClick={submitBatch}>
              일괄 등록
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
