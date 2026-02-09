import React, { useContext, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";
import { MemberContext } from "../../context/MemberContext";
import { CommunityAPI } from "../../api/communityApi";
import styles from "./CommunityDetail.module.css";

function formatDate(v) {
  if (!v) return "-";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return String(v);
  return d.toLocaleString();
}

export default function CommunityDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { stateCommunity, communityActions } = useContext(CommunityContext);

  const { stateMember } = useContext(MemberContext);
  const myMemberId = stateMember?.me?.member_id ?? stateMember?.me?.memberId ?? null;

  const [comments, setComments] = useState([]);
  const [commentText, setCommentText] = useState("");
  const [commentLoading, setCommentLoading] = useState(false);
  const [commentError, setCommentError] = useState("");
  const [page, setPage] = useState(0);

  const limit = 10;
  const offset = useMemo(() => page * limit, [page]);

  const [editingId, setEditingId] = useState(null);
  const [editingText, setEditingText] = useState("");
  const [editingSaving, setEditingSaving] = useState(false);
  const [activeToggling, setActiveToggling] = useState(false);

  useEffect(() => {
    communityActions.fetchDetail(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  useEffect(() => {
    let mounted = true;

    const fetchComments = async () => {
      setCommentLoading(true);
      setCommentError("");
      try {
        const r = await CommunityAPI.comments(id, { limit, offset });
        const data = r.data;
        const list = Array.isArray(data) ? data : data?.items ?? [];
        if (mounted) setComments(list);
      } catch (e) {
        const status = e?.response?.status;
        if (status === 404 || status === 501) {
          if (mounted) {
            setComments([]);
            setCommentError("");
          }
        } else {
          if (mounted) setCommentError(e.message || "댓글 조회 실패");
        }
      } finally {
        if (mounted) setCommentLoading(false);
      }
    };

    if (id) fetchComments();
    return () => {
      mounted = false;
    };
  }, [id, limit, offset]);

  const onToggleActive = async () => {
    if (activeToggling) return;
    setActiveToggling(true);
    try {
      await CommunityAPI.toggleActive(id);
      await communityActions.fetchDetail(id);
    } catch (e) {
      alert(e?.response?.data?.detail || e?.message || "공개 설정 변경 실패");
    } finally {
      setActiveToggling(false);
    }
  };

  const onSubmitComment = async () => {
    const content = commentText.trim();
    if (!content) return;

    try {
      const r = await CommunityAPI.createComment(id, { content });
      const saved = r.data;
      setComments((prev) => [saved, ...prev].slice(0, limit));
      setCommentText("");
    } catch (e) {
      const status = e?.response?.status;
      if (status === 404 || status === 501) {
        alert("댓글 등록 API가 아직 준비되지 않았습니다. (백엔드 구현 후 연결)");
      } else {
        alert(e.message || "댓글 등록 실패");
      }
    }
  };

  const startEdit = (c) => {
    setEditingId(c.comment_id ?? c.id);
    setEditingText(c.content ?? "");
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditingText("");
    setEditingSaving(false);
  };

  const saveEdit = async () => {
    const content = editingText.trim();
    if (!editingId || !content || editingSaving) return;

    setEditingSaving(true);
    try {
      const r = await CommunityAPI.updateComment(id, editingId, { content });
      const updated = r.data;

      setComments((prev) =>
        prev.map((c) => {
          const cid = c.comment_id ?? c.id;
          if (Number(cid) !== Number(editingId)) return c;
          return { ...c, ...updated };
        })
      );

      cancelEdit();
    } catch (e) {
      alert(e.message || "댓글 수정 실패");
      setEditingSaving(false);
    }
  };

  const d = stateCommunity.detail;

  const imageUrls = d?.image_urls ?? (d?.imageUrl ? [d.imageUrl] : d?.image_url ? [d.image_url] : []);
  const nickname = d?.nickname ?? "-";
  const createdAt = formatDate(d?.created_at ?? d?.createdAt);
  const recommend = d?.recommend ?? 0;
  const communityActive = d?.community_active ?? true;
  const ownerId = d?.member_id ?? null;
  const isMine = myMemberId != null && ownerId != null && Number(myMemberId) === Number(ownerId);

  const [liked, setLiked] = useState(false);
  const [heartAnim, setHeartAnim] = useState(false);

  useEffect(() => {
    if (d) setLiked(d?.liked ?? d?.recommended ?? false);
  }, [d]);

  const onRecommend = async () => {
    try {
      const out = await communityActions.recommendToggle(id);
      console.log("recommendToggle response(detail):", out);
      const nowLiked = out?.data?.recommended ?? !liked;
      setLiked(nowLiked);
      if (nowLiked) {
        setHeartAnim(true);
        setTimeout(() => setHeartAnim(false), 600);
      }
      await communityActions.fetchDetail(id);
    } catch (e) {
      alert(e?.response?.data?.detail || e?.message || "추천 실패");
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h1>{d ? `${nickname}님의 게시글` : "로딩 중..."}</h1>
      </div>

      {stateCommunity.error && <div className={styles.errorBox}>{stateCommunity.error}</div>}
      {!d ? (
        <div>Loading...</div>
      ) : (
        <>
          <div className={styles.communityDetailCard}>
            {/* 모든 AI 생성 이미지 표시 */}
            {imageUrls.length > 0 ? (
              <div className={styles.communityDetailImages}>
                {imageUrls.map((url, idx) => (
                  <div key={idx} className={styles.communityDetailThumb}>
                    <img src={url} alt={`community-${idx + 1}`} />
                  </div>
                ))}
              </div>
            ) : (
              <div className={styles.communityDetailThumb}>
                <div className={styles.communityCardThumbPlaceholder}>NO IMAGE</div>
              </div>
            )}

            <div className={styles.communityDetailMeta}>
              <div className={styles.metaTop}>
                <div className={styles.metaLeft}>
                  <div className={styles.communityCardNickname}>{nickname}</div>
                  <div className={styles.communityCardDate}>{createdAt}</div>
                </div>

                <div className={styles.metaRight}>
                  {isMine && (
                    <div
                      className={styles.activeToggle}
                      onClick={onToggleActive}
                      style={{ cursor: activeToggling ? "not-allowed" : "pointer" }}
                    >
                      <span className={styles.activeToggleLabel}>공개</span>
                      <div className={`${styles.toggleSwitch} ${communityActive ? styles.toggleOn : styles.toggleOff}`}>
                        <div className={styles.toggleKnob} />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className={styles.likeRow}>
                <button
                  type="button"
                  onClick={onRecommend}
                  className={styles.likeBtn}
                >
                  <span className={`${styles.heartIcon} ${liked ? styles.heartActive : ""} ${heartAnim ? styles.heartBounce : ""}`}>
                    {liked ? "♥" : "♡"}
                  </span>
                </button>
                <span className={styles.likeCount}>
                  {recommend > 0 ? `좋아요 ${recommend}개` : ""}
                </span>
              </div>
            </div>
          </div>

          <div className={styles.commentBox}>
            <div className={styles.commentHeader}>
              <h3>댓글</h3>
              <div className={styles.commentPager}>
                <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}>
                  이전
                </button>
                <span>{page + 1}</span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={commentLoading || comments.length < limit}
                >
                  다음
                </button>
              </div>
            </div>

            {commentError && <div className={styles.errorBox}>{commentError}</div>}
            {commentLoading && <div>댓글 불러오는 중...</div>}

            {!commentLoading && !commentError && comments.length === 0 && (
              <div className={styles.notice}>댓글이 없습니다.</div>
            )}

            <div className={styles.commentList}>
              {comments.map((c) => {
                const cid = c.comment_id ?? c.id;
                const cnick = c.nickname ?? "-";
                const cdate = formatDate(c.created_at ?? c.createdAt);
                const ctext = c.content ?? "";

                const ownerId = c.member_id ?? c.memberId ?? null;
                const isMine =
                  myMemberId != null && ownerId != null && Number(myMemberId) === Number(ownerId);

                const isEditing = editingId != null && Number(editingId) === Number(cid);

                return (
                  <div className={styles.commentItem} key={cid}>
                    <div className={styles.commentItemMeta}>
                      <div className={styles.commentNick}>{cnick}</div>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <div className={styles.commentDate}>{cdate}</div>

                        {isMine && !isEditing && (
                          <button type="button" onClick={() => startEdit(c)} className={styles.commentEditBtn}>
                            수정
                          </button>
                        )}
                      </div>
                    </div>

                    {isEditing ? (
                      <div className={styles.commentEditArea}>
                        <textarea
                          rows={3}
                          value={editingText}
                          onChange={(e) => setEditingText(e.target.value)}
                        />
                        <div className={styles.commentEditActions}>
                          <button type="button" onClick={cancelEdit} disabled={editingSaving}>
                            취소
                          </button>
                          <button
                            type="button"
                            onClick={saveEdit}
                            disabled={editingSaving || !editingText.trim()}
                          >
                            {editingSaving ? "저장 중..." : "저장"}
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className={styles.commentText}>{ctext}</div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className={styles.commentForm}>
              <textarea
                rows={3}
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="댓글을 입력하세요"
                disabled={editingId != null}
              />
              <button
                onClick={onSubmitComment}
                disabled={!commentText.trim() || editingId != null}
                className={styles.commentFormSubmit}
              >
                댓글 등록
              </button>
              <div className={styles.commentHint}>* 본인 댓글은 수정 가능합니다.</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
