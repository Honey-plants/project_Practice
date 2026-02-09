from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, Index, text
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from backend.app.core.database import Base

class CommunityRecommend(Base):
    __tablename__ = "community_recommend"

    recommend_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    community_id: Mapped[int] = mapped_column(
        ForeignKey("community.community_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    member_id: Mapped[int] = mapped_column(
        ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        # 한 사람이 한 커뮤니티에 좋아요는 1번만 가능
        UniqueConstraint("community_id", "member_id", name="uq_community_member_recommend"),
        Index("idx_recommend_community", "community_id"),
        Index("idx_recommend_member", "member_id"),
    )
