import React, { useContext, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";
import { MemberContext } from "../../context/MemberContext";
import { CommunityAPI } from "../../api/communityApi";
import "../../styles/Community.css";
import "../../styles/CommunityDetail.css";

function formatDate(v) {
  if (!v) return "-";
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return String(v);
  return d.toLocaleString();
}
import { AuthContext } from "../../context/AuthContext";
import { MemberContext } from "../../context/MemberContext";
import api from "../../api/axiosInstance";
import "../../styles/CommunityDetail.css";

export default function CommunityDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
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

  useEffect(() => {
    if (!stateAuth.accessToken) return;
    communityActions.fetchDetail(id);
    setComments([]);
    setCommentInput("");

    // 댓글 목록 조회 시도 (백엔드 comment API 준비 시 실제 동작)
    api.get(`/community/${id}/comments`)
      .then((r) => {
        const list = Array.isArray(r.data) ? r.data : r.data?.items ?? [];
        setComments(list);
      })
      .catch(() => {
        // 엔드포인트 미준비 → 빈 목록 유지
      });
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

  const onDelete = async () => {
    alert("삭제는 현재 API 연결이 주석처리되어 있습니다.");
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

  const img = d?.image_urls?.[0] ?? d?.imageUrl ?? d?.image_url ?? "";
  const nickname = d?.nickname ?? "-";
  const createdAt = formatDate(d?.created_at ?? d?.createdAt);
  const recommend = d?.recommend ?? 0;

  // ✅ 추천 클릭 -> 토글 -> 상세 재조회
  const onRecommend = async () => {
    try {
      const out = await communityActions.recommendToggle(id);
      console.log("recommendToggle response(detail):", out);
      await communityActions.fetchDetail(id);
    } catch (e) {
      alert(e?.response?.data?.detail || e?.message || "추천 실패");
    }
  };

  return (
    <div className="container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h1>Community Detail</h1>
        <div style={{ display: "flex", gap: 8 }}>
          <Link to={`/community/${id}/edit`}>Edit</Link>
          <button onClick={onDelete}>Delete</button>
        </div>

        {/* 공개/비공개 ON/OFF 스위치 — 작성자에게만 표시 */}
        {isOwner && (
          <div className="switchRow">
            <span className="switchLabel">{isActive ? "공개" : "비공개"}</span>
            <div
              className={`switchTrack ${isActive ? "switchOn" : "switchOff"}`}
              onClick={toggleLoading ? undefined : handleToggleActive}
              role="switch"
              aria-checked={isActive}
            >
              <div className="switchThumb" />
            </div>
          </div>
        )}
      </div>

      {stateCommunity.error && <div className="errorBox">{stateCommunity.error}</div>}
      {!d ? (
        <div>Loading...</div>
      ) : (
        <>
          <div className="communityDetailCard">
            <div className="communityDetailThumb">
              {img ? (
                <img src={img} alt="community" />
              ) : (
                <div className="communityCardThumbPlaceholder">NO IMAGE</div>
              )}
            </div>

            <div className="communityDetailMeta">
              <div className="communityCardNickname">{nickname}</div>
              <div className="communityCardDate">{createdAt}</div>

              <div style={{ marginTop: 10 }}>
                <button
                  type="button"
                  onClick={onRecommend}
                  style={{
                    padding: "6px 10px",
                    borderRadius: 10,
                    border: "1px solid #ddd",
                    background: "#fff",
                    cursor: "pointer",
                    fontSize: 12,
                  }}
                >
                  👍 {recommend}
                </button>
              </div>
            </div>
          </div>

          <div className="commentBox">
            <div className="commentHeader">
              <h3 style={{ margin: 0 }}>댓글</h3>
              <div className="commentPager">
                <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}>
                  이전
                </button>
                <span style={{ fontSize: 12, color: "#666" }}>{page + 1}</span>
                <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={commentLoading || comments.length < limit}
                >
                  다음
                </button>
              </div>
            </div>

            {commentError && <div className="errorBox">{commentError}</div>}
            {commentLoading && <div>댓글 불러오는 중...</div>}

            {!commentLoading && !commentError && comments.length === 0 && (
              <div className="notice">댓글이 없습니다.</div>
            )}

            <div className="commentList">
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
                  <div className="commentItem" key={cid}>
                    <div className="commentItemMeta">
                      <div className="commentNick">{cnick}</div>
                      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        <div className="commentDate">{cdate}</div>

                        {isMine && !isEditing && (
                          <button type="button" onClick={() => startEdit(c)} style={{ fontSize: 12 }}>
                            수정
                          </button>
                        )}
                      </div>
                    </div>

                    {isEditing ? (
                      <div style={{ display: "grid", gap: 8 }}>
                        <textarea
                          rows={3}
                          value={editingText}
                          onChange={(e) => setEditingText(e.target.value)}
                        />
                        <div style={{ display: "flex", gap: 8 }}>
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
                      <div className="commentText">{ctext}</div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="commentForm">
              <textarea
                rows={3}
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="댓글을 입력하세요"
                disabled={editingId != null}
              />
              <button onClick={onSubmitComment} disabled={!commentText.trim() || editingId != null}>
                댓글 등록
              </button>
              <div className="commentHint">* 본인 댓글은 수정 가능합니다.</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
