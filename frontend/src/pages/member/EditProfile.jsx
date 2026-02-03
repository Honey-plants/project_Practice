import { useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { MemberContext } from "../../context/MemberContext";
import { MetaContext } from "../../context/MetaContext";
import { MemberAPI } from "../../api/memberApi";
import RestrictionsPicker from "../../components/restrictions/RestrictionsPicker";
import styles from "./EditProfile.module.css";

/**
 * EditProfile
 * - 닉네임 수정 및 제한 아이템(item_ids) 수정 페이지
 * - 저장 시 PATCH /member/me 호출
 */
export default function EditProfile() {
  const nav = useNavigate();
  const { stateMember, memberActions } = useContext(MemberContext);
  const { stateMeta, metaActions } = useContext(MetaContext);

  const me = stateMember.me;
  const categories = useMemo(() => stateMeta?.restrictions || [], [stateMeta?.restrictions]);

  // Form state
  const [form, setForm] = useState({
    nickname: "",
    item_ids: [],
  });

  const [dislikes, setDislikes] = useState([]);
  const [dislikeInput, setDislikeInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");
  const [msgType, setMsgType] = useState(""); // "success" or "error"

  // me 데이터가 로드되면 form 초기화
  useEffect(() => {
    if (!me) return;
    setForm({
      nickname: me.nickname || "",
      item_ids: Array.isArray(me.item_ids) ? me.item_ids : [],
    });
    setDislikes(Array.isArray(me.dislike_tags) ? me.dislike_tags : []);
  }, [me]);

  // meta 데이터 로드
  useEffect(() => {
    if (!stateMeta?.loading && categories.length === 0) {
      metaActions?.refresh?.({ force: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 닉네임 변경 핸들러
  const handleNicknameChange = (e) => {
    setForm((prev) => ({ ...prev, nickname: e.target.value }));
  };

  // 제한 아이템 토글 핸들러
  const handleToggleItem = (id) => {
    setForm((prev) => {
      const itemSet = new Set(prev.item_ids || []);
      if (itemSet.has(id)) {
        itemSet.delete(id);
      } else {
        itemSet.add(id);
      }
      return { ...prev, item_ids: Array.from(itemSet) };
    });
  };

  // Dislike 관련 핸들러
  const addDislike = () => {
    const trimmed = dislikeInput.trim();
    if (!trimmed) return;
    if (dislikes.length >= 3) {
      setMsg("최대 3개까지만 추가할 수 있습니다");
      setMsgType("error");
      return;
    }
    if (dislikes.includes(trimmed)) {
      setMsg("이미 추가된 재료입니다");
      setMsgType("error");
      return;
    }
    setDislikes([...dislikes, trimmed]);
    setDislikeInput("");
    setMsg("");
  };

  const removeDislike = (index) => {
    setDislikes(dislikes.filter((_, i) => i !== index));
  };

  const handleDislikeKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addDislike();
    }
  };

  // 저장 핸들러
  const handleSave = async () => {
    setMsg("");
    setMsgType("");
    setSaving(true);

    try {
      const payload = {
        nickname: form.nickname?.trim() || null,
        item_ids: form.item_ids || [],
        dislike_tags: dislikes.length > 0 ? dislikes : null,
      };

      await MemberAPI.updateMe(payload);
      await memberActions.loadMe();

      // 즉시 이동 (로딩 없이)
      nav("/member/profile");
    } catch (error) {
      const errorMsg = error?.response?.data?.detail || error?.message || "저장에 실패했습니다";
      setMsg(errorMsg);
      setMsgType("error");
    } finally {
      setSaving(false);
    }
  };

  // 취소 핸들러
  const handleCancel = () => {
    nav("/member/profile");
  };

  if (!me) {
    return <div className={styles.container}>Loading...</div>;
  }

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>Profile Edit</h2>

      {msg && (
        <div className={`${styles.message} ${msgType === "success" ? styles.messageSuccess : styles.messageError}`}>
          {msg}
        </div>
      )}

      <div className={styles.card}>
        <div className={styles.formGroup}>
          <div className={styles.inputWrapper}>
            <label className={styles.label}>Nickname</label>
            <input
              type="text"
              name="nickname"
              value={form.nickname}
              onChange={handleNicknameChange}
              className={styles.input}
              placeholder="Please enter your nickname"
            />
          </div>
        </div>
      </div>

      <div className={styles.sectionHeader}>
        <h3 className={styles.sectionTitle}>Restricted information</h3>
        <div className={styles.selectedCount}>
          선택: <span className={styles.selectedCountNumber}>{form.item_ids.length}</span>개
        </div>
      </div>

      {stateMeta?.loading && <div className={styles.loading}>Category Loading...</div>}
      {stateMeta?.error && <div className={styles.errorBox}>{stateMeta.error}</div>}

      <RestrictionsPicker
        categories={categories}
        selectedIds={form.item_ids}
        onToggle={handleToggleItem}
        mode="select"
        onlyActive={true}
      />

      <div className={styles.sectionHeader}>
        <h3 className={styles.sectionTitle}>Dislike Ingredients (최대 3개)</h3>
      </div>

      <div className={styles.card}>
        <div className={styles.formGroup}>
          <div className={styles.inputWrapper}>
            <label className={styles.label}>재료 추가</label>
            <div style={{ display: "flex", gap: 8 }}>
              <input
                type="text"
                value={dislikeInput}
                onChange={(e) => setDislikeInput(e.target.value)}
                onKeyDown={handleDislikeKeyDown}
                placeholder="e.g. 고수 (Enter 또는 추가 버튼 클릭)"
                maxLength={50}
                disabled={dislikes.length >= 3}
                className={styles.input}
                style={{ flex: 1 }}
              />
              <button
                type="button"
                onClick={addDislike}
                disabled={!dislikeInput.trim() || dislikes.length >= 3}
                className={`${styles.button} ${styles.buttonSecondary}`}
              >
                추가
              </button>
            </div>
          </div>

          {dislikes.length > 0 && (
            <div className={styles.dislikeTagsContainer}>
              {dislikes.map((dislike, index) => (
                <div className={styles.dislikeTag} key={index}>
                  <span>{dislike}</span>
                  <button
                    type="button"
                    className={styles.dislikeRemoveBtn}
                    onClick={() => removeDislike(index)}
                    aria-label="Remove"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className={styles.dislikeCounter}>
            {dislikes.length} / 3 재료 추가됨
          </div>
        </div>
      </div>

      <div className={styles.buttonWrapper}>
        <button
          onClick={handleCancel}
          className={`${styles.button} ${styles.buttonSecondary}`}
          disabled={saving}
        >
          취소
        </button>
        <button
          onClick={handleSave}
          className={`${styles.button} ${styles.buttonPrimary}`}
          disabled={saving}
        >
          {saving ? "저장 중..." : "저장"}
        </button>
      </div>
    </div>
  );
}