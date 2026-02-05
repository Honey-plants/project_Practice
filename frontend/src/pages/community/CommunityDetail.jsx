import React, { useContext, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";
import { MemberContext } from "../../context/MemberContext";
import api from "../../api/axiosInstance";
import "../../styles/CommunityDetail.css";

export default function CommunityDetail() {
  const { id } = useParams();
  const { stateCommunity, communityActions } = useContext(CommunityContext);
  const { stateMember } = useContext(MemberContext);

  const myMemberId = stateMember?.me?.member_id;
  const myNickname = stateMember?.me?.nickname;

  const [toggleLoading, setToggleLoading] = useState(false);
  const [comments, setComments] = useState([]);
  const [commentInput, setCommentInput] = useState("");
  const [commentLoading, setCommentLoading] = useState(false);

  useEffect(() => {
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

  const d = stateCommunity.detail;
  if (!d) return <div className="loading">Loading...</div>;

  const isOwner = d.member_id === myMemberId;
  const nickname = isOwner && myNickname ? myNickname : `#${d.member_id}`;
  const isActive = d.community_active;

  const handleToggleActive = async () => {
    setToggleLoading(true);
    try {
      await communityActions.toggleActive(id, !isActive);
    } finally {
      setToggleLoading(false);
    }
  };

  // 댓글 제출
  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    const text = commentInput.trim();
    if (!text || commentLoading) return;

    setCommentLoading(true);

    // 낙관적 업데이트 — 즉시 UI에 표시
    const optimistic = {
      comment_id: Date.now(),
      content: text,
      member_id: myMemberId,
      nickname: myNickname || `#${myMemberId}`,
      created_at: new Date().toISOString(),
    };
    setComments((prev) => [...prev, optimistic]);
    setCommentInput("");

    try {
      // 백엔드 API 호출 시도 (엔드포인트가 준비되면 실제 저장됨)
      await api.post(`/community/${id}/comments`, { content: text });
    } catch {
      // 엔드포인트 미준비 시 로컬만 유지
    } finally {
      setCommentLoading(false);
    }
  };

  return (
    <div className="communityDetail">
      {/* 이미지 */}
      {d.image_urls?.length > 0 && (
        <div className="imageBox">
          {d.image_urls.map((src, i) => (
            <img key={i} src={src} alt={`community-${i}`} />
          ))}
        </div>
      )}

      {/* 작성자 정보 + 좋아요 + 공개 토글 */}
      <div className="detailHeader">
        <div className="authorRow">
          <div className="authorAvatar">{nickname.charAt(0)}</div>
          <div className="authorInfo">
            <span className="authorName">{nickname}</span>
            <span className="authorLike">
              <span className="likeIcon">♥</span> {d.recommend ?? 0}
            </span>
          </div>
        </div>

        {/* 공개/비공개 토글 — 작성자에게만 표시 */}
        {isOwner && (
          <button
            className={`toggleBtn ${isActive ? "toggleOn" : "toggleOff"}`}
            onClick={handleToggleActive}
            disabled={toggleLoading}
          >
            {toggleLoading ? "..." : isActive ? "공개" : "비공개"}
          </button>
        )}
      </div>

      {/* 댓글 영역 */}
      <div className="commentBox">
        <div className="commentTitle">댓글</div>

        {/* 댓글 목록 */}
        {comments.length === 0 && (
          <div className="commentEmpty">아직 달린 댓글이 없습니다.</div>
        )}
        {comments.map((c, i) => {
          const cNick = c.nickname
            || (c.member_id === myMemberId && myNickname ? myNickname : `#${c.member_id}`);
          return (
            <div key={c.comment_id ?? i} className="comment">
              <div className="commentAvatar">{cNick.charAt(0)}</div>
              <div className="commentContent">
                <span className="commentAuthor">{cNick}</span>
                <span className="commentText">{c.content}</span>
              </div>
            </div>
          );
        })}

        {/* 댓글 입력폼 — 로그인 유저에게만 표시 */}
        {myMemberId && (
          <form className="commentForm" onSubmit={handleCommentSubmit}>
            <input
              className="commentInput"
              type="text"
              placeholder="댓글을 남기세요..."
              value={commentInput}
              onChange={(e) => setCommentInput(e.target.value)}
              disabled={commentLoading}
            />
            <button
              className="commentSubmitBtn"
              type="submit"
              disabled={!commentInput.trim() || commentLoading}
            >
              {commentLoading ? "..." : "등록"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
