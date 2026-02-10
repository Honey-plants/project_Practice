from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.app.models.comment import Comment
from backend.app.models.community import Community
from backend.app.models.member import Member

DELETED_COMMENT_TEXT = "댓글이 삭제되었습니다."


def list_comments(
    db: Session,
    *,
    community_id: int,
    limit: int = 10,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """커뮤니티 댓글 최신순 조회 (기본: 10개)."""

    limit = max(1, min(int(limit or 10), 50))
    offset = max(0, int(offset or 0))

    # community 존재 체크
    exists = db.execute(
        select(Community.community_id).where(Community.community_id == int(community_id))
    ).scalar_one_or_none()
    if not exists:
        raise HTTPException(status_code=404, detail="Community not found")

    stmt = (
        select(Comment, Member.nickname)
        .join(Member, Member.member_id == Comment.member_id, isouter=True)  # 탈퇴/NULL 대비
        .where(Comment.community_id == int(community_id))
        .order_by(Comment.comment_id.desc())  # 최신순
        .offset(offset)
        .limit(limit)
    )

    rows = db.execute(stmt).all()
    if not rows:
        return []

    out: List[Dict[str, Any]] = []
    for c, nickname in rows:
        # member가 삭제되어 join이 안되면 nickname None일 수 있음
        out.append(
            {
                "comment_id": c.comment_id,
                "community_id": c.community_id,
                "member_id": c.member_id,
                "nickname": nickname or "삭제된 사용자",
                "content": c.content,
                "created_at": c.create_at.isoformat() if getattr(c, "create_at", None) else None,
                "updated_at": c.update_at.isoformat() if getattr(c, "update_at", None) else None,
            }
        )
    return out


def create_comment(
    db: Session,
    *,
    community_id: int,
    member_id: int,
    content: str,
) -> Dict[str, Any]:
    text = (content or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="content is required")

    exists = db.execute(
        select(Community.community_id).where(Community.community_id == int(community_id))
    ).scalar_one_or_none()
    if not exists:
        raise HTTPException(status_code=404, detail="Community not found")

    c = Comment(
        content=text,
        member_id=int(member_id),
        community_id=int(community_id),
    )
    db.add(c)
    db.flush()

    nickname = db.execute(
        select(Member.nickname).where(Member.member_id == int(member_id))
    ).scalar_one_or_none() or ""

    return {
        "comment_id": c.comment_id,
        "community_id": c.community_id,
        "member_id": c.member_id,
        "nickname": nickname or "삭제된 사용자",
        "content": c.content,
        "created_at": c.create_at.isoformat() if getattr(c, "create_at", None) else None,
        "updated_at": c.update_at.isoformat() if getattr(c, "update_at", None) else None,
    }


def update_comment(
    db: Session,
    *,
    community_id: int,
    comment_id: int,
    member_id: int,
    content: str,
) -> Dict[str, Any]:
    """댓글 수정: 본인만 가능"""

    text = (content or "").strip()
    if not text:
        raise HTTPException(status_code=422, detail="content is required")

    c: Optional[Comment] = db.execute(
        select(Comment)
        .where(Comment.comment_id == int(comment_id))
        .where(Comment.community_id == int(community_id))
    ).scalar_one_or_none()

    if not c:
        raise HTTPException(status_code=404, detail="Comment not found")

    # 탈퇴 처리된 댓글은 수정 불가(원하면 허용할 수도 있음)
    if c.content == DELETED_COMMENT_TEXT:
        raise HTTPException(status_code=409, detail="Deleted comment cannot be updated")

    if int(c.member_id or 0) != int(member_id):
        raise HTTPException(status_code=403, detail="Not allowed")

    c.content = text
    db.flush()

    nickname = db.execute(
        select(Member.nickname).where(Member.member_id == int(member_id))
    ).scalar_one_or_none() or ""

    return {
        "comment_id": c.comment_id,
        "community_id": c.community_id,
        "member_id": c.member_id,
        "nickname": nickname or "삭제된 사용자",
        "content": c.content,
        "created_at": c.create_at.isoformat() if getattr(c, "create_at", None) else None,
        "updated_at": c.update_at.isoformat() if getattr(c, "update_at", None) else None,
    }


def anonymize_comments_by_member(
    db: Session,
    *,
    member_id: int,
) -> int:
    """
    회원 탈퇴 시:
    - 댓글은 삭제하지 않고
    - content를 '댓글이 삭제되었습니다.'로 변경
    - member_id는 NULL로 바꿔서 FK 문제/조인 문제 방지
    반환: 변경된 row 수
    """
    res = db.execute(
        update(Comment)
        .where(Comment.member_id == int(member_id))
        .values(content=DELETED_COMMENT_TEXT, member_id=None)
    )
    return int(res.rowcount or 0)
