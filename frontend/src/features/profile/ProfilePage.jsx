import Modal from "../../common/components/ui/Modal";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Header from "../../common/components/ui/Header";
import "./ProfilePage.css"

import { getSession, setSession as persistSession, subscribeSession } from "../../common/utils/session";
import { getMember, updateMember } from "../../common/utils/memberApi";

export default function ProfilePage() {
  const { memberId } = useParams();
  const navigate = useNavigate();

  const [session, setSessionState] = useState(() => getSession());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [profile, setProfile] = useState(null);
  const [nickname, setNickname] = useState("");

  useEffect(() => subscribeSession(setSessionState), []);

  const myId = session?.member_id;
  const token = session?.access_token;

  useEffect(() => {
    if (!token || !myId) {
      navigate("/login", { replace: true });
      return;
    }
    if (!memberId) navigate(`/profile/${myId}`, { replace: true });
  }, [memberId, myId, token, navigate]);

  useEffect(() => {
    if (!token || !myId || !memberId) return;
    if (String(myId) !== String(memberId)) {
      navigate(`/profile/${myId}`, { replace: true });
    }
  }, [memberId, myId, token, navigate]);

  const effectiveId = useMemo(() => memberId || myId, [memberId, myId]);

  useEffect(() => {
    let ignore = false;
    const run = async () => {
      if (!token || !effectiveId) return;
      setLoading(true);
      setError("");
      try {
        const data = await getMember(effectiveId);
        if (ignore) return;
        setProfile(data);
        setNickname(data?.nickname ?? "");
      } catch (e) {
        if (ignore) return;
        setError(e?.message || "프로필 조회 실패");
        if (e?.status === 401) navigate("/login", { replace: true });
      } finally {
        if (!ignore) setLoading(false);
      }
    };
    run();
    return () => { ignore = true; };
  }, [effectiveId, token, navigate]);

const [editOpen, setEditOpen] = useState(false);
const [editNick, setEditNick] = useState("");
const [editItemIds, setEditItemIds] = useState([]);
const [editDislikeTags, setEditDislikeTags] = useState([]);

const openEdit = () => {
  // profile 로딩 후 값으로 프리필
  setEditNick(profile?.nickname ?? "");
  setEditItemIds(profile?.item_ids ?? []);
  setEditDislikeTags(profile?.dislike_tags ?? []);
  setEditOpen(true);
};

const closeEdit = () => setEditOpen(false);

const toggleItem = (id) => {
  setEditItemIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
};


const onSaveEdit = async () => {
  setError("");
  try {
    if (!token || !effectiveId) return navigate("/login");

    const updated = await updateMember(effectiveId, {
      nickname: editNick,
      item_ids: editItemIds,
      dislike_tags: editDislikeTags,
    });

    setProfile(updated);
    setNickname(updated?.nickname ?? editNick);

    // Header 즉시 반영
    const current = getSession(); // ✅ localStorage에 있는 진짜 세션을 다시 읽음
      persistSession({
        ...current, // ✅ access_token, member_id 보존
        nickname: updated?.nickname ?? editNick,
    });

    setEditOpen(false);
    alert("저장 완료");
  } catch (e) {
    setError(e?.message || "저장 실패");
    if (e?.status === 401) navigate("/login");
  }
};

  // 좌측 메뉴 이동
  const goReviewList = () => navigate("/review");
  const goCommunity = () => navigate("/community");
  const goEdit = () => openEdit();

  

return (
  <div className="pfp-root">
    <Header showNav={true} showAuthArea={true} />

    <div className="pfp-shell">
      <div className="pfp-grid">
        {/* LEFT SIDEBAR */}
        <aside className="pfp-aside">
          <div className="pfp-asideTop">
            <div className="pfp-title">Profile</div>
          </div>

          <div className="pfp-card">
            {loading ? (
              <div className="pfp-muted">불러오는 중...</div>
            ) : (
              <>
                <div className="pfp-infoRow">{profile?.nickname ?? "-"}</div>
                <div className="pfp-infoRow">{profile?.email ?? "-"}</div>
              </>
            )}
          </div>

          <div className="pfp-card pfp-menu">
            <button className="pfp-menuBtn" type="button" onClick={goReviewList}>
              리뷰 리스트
            </button>
            <button className="pfp-menuBtn" type="button" onClick={goCommunity}>
              커뮤니티
            </button>
            <button className="pfp-menuBtn" type="button" onClick={goEdit}>
              회원정보 수정
            </button>
          </div>
        </aside>

        {/* RIGHT MAIN */}
        <section className="pfp-main">
          {error && <div className="pfp-error">{error}</div>}

          <div className="pfp-map">
            내가 다닌 장소를 표시하는 지도
            <br />
            보이는 위치
          </div>

          <div className="pfp-row">
            <div className="pfp-panel">
              <button className="pfp-more" type="button" onClick={goReviewList}>
                더보기
              </button>
              <div className="pfp-panelText">
                내가 작성한
                <br />
                리뷰 리스트
              </div>
            </div>

            <div className="pfp-panel">
              <button className="pfp-more" type="button" onClick={goCommunity}>
                더보기
              </button>
              <div className="pfp-panelText">
                나의 리뷰
                <br />
                기반으로 만든
                <br />
                커뮤니티 글
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
    {editOpen && (
      <Modal title="회원정보 수정" onClose={closeEdit}>
        <div className="pfp-edit">
          <div className="pfp-formRow">
            <label>닉네임</label>
            <input value={editNick} onChange={(e) => setEditNick(e.target.value)} />
          </div>

          {/* {RESTRICTION_CATEGORIES?.map((cat) => (
            <div key={cat.id} className="pfp-formBlock">
              <div className="pfp-formTitle">{cat.label}</div>
              <div className="pfp-chipGrid">
                {cat.options.map((opt) => (
                  <button
                    key={opt.itemId}
                    type="button"
                    className={`pfp-chip ${editItemIds.includes(opt.itemId) ? "on" : ""}`}
                    onClick={() => toggleItem(opt.itemId)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          ))} */}

          <div className="pfp-actions">
            <button type="button" onClick={onSaveEdit}>저장</button>
            <button type="button" onClick={closeEdit}>취소</button>
          </div>
        </div>
      </Modal>
    )}
  </div>
);

}
