from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, Index, text,
)
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class Review(Base):
    __tablename__ = "review"

    review_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_title: Mapped[str] = mapped_column(String(255), nullable=False)
    review_content: Mapped[str] = mapped_column(Text, nullable=False)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[str] = mapped_column(String(100), nullable=False)

    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), server_onupdate=text("CURRENT_TIMESTAMP"))

    # 커뮤니티 등록 여부 :: T 미사용 / F 사용
    available: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))

    menu_name: Mapped[str] = mapped_column(String(255), nullable=False)

    # 해당 유저의 식성 정보
    review_items: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    member_id: Mapped[int] = mapped_column(ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    # 관계 모델 / 테이블
    member: Mapped["Member"] = relationship("Member", back_populates="review")

    # review_id = Column(Integer, primary_key=True, autoincrement=True)
    # review_title = Column(Text, nullable=False)
    # review_content = Column(Text, nullable=False)
    # rating = Column(Integer, nullable=True)
    # location = Column(String(100), nullable=True)
    # create_review = Column(DateTime, nullable=False, server_default=func.now())
    # member_id = Column(Integer, ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    #
    # member = relationship("Member", back_populates="review")

    __table_args__ = (
        Index("idx_review_member_id", "member_id"),
    )