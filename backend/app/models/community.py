from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, Index, text,
)
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class Community(Base):
    __tablename__ = "community"

    community_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), server_onupdate=text("CURRENT_TIMESTAMP"))

    recommend: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    community_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))

    member_id: Mapped[int] = mapped_column(ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    # 관계 모델 / 테이블
    member: Mapped["Member"] = relationship("Member", back_populates="community")
    comment: Mapped[List["Comment"]] = relationship("Comment", back_populates="community", passive_deletes=True)

    __table_args__ = (
        Index("idx_community_member_id", "member_id"),
    )