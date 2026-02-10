from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security.deps import get_current_member
from backend.app.features.comment.schemas import CommentCreate, CommentRead, CommentUpdate
from backend.app.features.comment import service

router = APIRouter(prefix="/community", tags=["comment"])


@router.get("/{community_id}/comments", response_model=list[CommentRead])
def list_community_comments(
    community_id: int,
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    return service.list_comments(db, community_id=community_id, limit=limit, offset=offset)


@router.post("/{community_id}/comments", response_model=CommentRead)
def create_community_comment(
    community_id: int,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    current=Depends(get_current_member),
):
    out = service.create_comment(
        db,
        community_id=community_id,
        member_id=current.member_id,
        content=payload.content,
    )
    db.commit()
    return out


# 댓글 수정
@router.put("/{community_id}/comments/{comment_id}", response_model=CommentRead)
def update_community_comment(
    community_id: int,
    comment_id: int,
    payload: CommentUpdate,
    db: Session = Depends(get_db),
    current=Depends(get_current_member),
):
    out = service.update_comment(
        db,
        community_id=community_id,
        comment_id=comment_id,
        member_id=current.member_id,
        content=payload.content,
    )
    db.commit()
    return out
