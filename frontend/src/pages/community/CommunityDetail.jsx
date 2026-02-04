import React, { useContext, useEffect } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { CommunityContext } from "../../context/CommunityContext";
import "../../styles/CommunityDetail.css";

export default function CommunityDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { stateCommunity, communityActions } = useContext(CommunityContext);

  useEffect(() => {
    communityActions.fetchDetail(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onDelete = async () => {
    await communityActions.remove(id);
    nav("/community");
  };

  const d = stateCommunity.detail;

  if (!d) return <div className="loading">Loading...</div>;

  return (
    <div className="communityDetail">
      {/* Header */}
      <div className="detailHeader">
        <div className="author">👤 user #{d.member_id}</div>
        <div className="actions">
          <Link to={`/community/${id}/edit`}>Edit</Link>
          <button onClick={onDelete}>Delete</button>
        </div>
      </div>

      {/* Images */}
      {d.image_urls?.length > 0 && (
        <div className="imageBox">
          {d.image_urls.map((src, i) => (
            <img key={i} src={src} alt={`community-${i}`} />
          ))}
        </div>
      )}

      {/* Content */}
      <div className="contentBox">
        <p className="contentText">{d.community_content}</p>
        <div className="meta">
          <span>{d.created_at}</span>
        </div>
      </div>

      {/* Comments (UI only) */}
      <div className="commentBox">
        <div className="comment">
          <b>user123</b> 와 여기 진짜 가보고 싶다 😍
        </div>
        <div className="comment">
          <b>foodlover</b> 지도 템플릿 감성 미쳤다
        </div>

        <input
          className="commentInput"
          placeholder="Add a comment..."
          disabled
        />
      </div>
    </div>
  );
}
