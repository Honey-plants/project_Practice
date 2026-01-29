from sqlalchemy import (
    DateTime, ForeignKey, Integer, Text, Index, text,
)
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class Comment(Base):
    __tablename__ = "comment"

    comment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), server_onupdate=text("CURRENT_TIMESTAMP"))

    member_id: Mapped[int] = mapped_column(ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    community_id: Mapped[int] = mapped_column(ForeignKey("community.community_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    # 관계 모델 / 테이블
    member: Mapped["Member"] = relationship("Member", back_populates="comment")
    community: Mapped["Community"] = relationship("Community", back_populates="comment")

    __table_args__ = (
        Index("idx_community_member_id", "member_id"),
    )