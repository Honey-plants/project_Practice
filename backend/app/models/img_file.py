from sqlalchemy import (
    DateTime, ForeignKey, Integer, String, UniqueConstraint, Index,
    text, BigInteger, CheckConstraint
)
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class ImgFile(Base):
    __tablename__ = "img_file"

    file_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 원본 파일명
    origin_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # uuid 변환 파일명
    storage_key: Mapped[str] = mapped_column(String(255), nullable=False)
    # 파일 저장 경로
    storage_path: Mapped[str] = mapped_column(String(255), nullable=False)
    # 파일 타입 [jpg, png 등]
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    # 파일 bytes
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    # REVIEW 경우 최대 1, 2, 3 등록 :: 구분
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    # 'review' | 'community'
    owner_type: Mapped[str] = mapped_column(String(50), nullable=False)

    member_id: Mapped[int] = mapped_column(ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    # REVIEW / COMMUNITY :: member 삭제 시 한번에 삭제 위해 FK 추가
    review_id: Mapped[Optional[int]] = mapped_column(ForeignKey("review.review_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)
    community_id: Mapped[Optional[int]] = mapped_column(ForeignKey("community.community_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=True)

    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))

    # 관계(조회 편의용)
    member: Mapped["Member"] = relationship("Member", back_populates="img_file", passive_deletes=True)
    review: Mapped[Optional["Review"]] = relationship("Review", passive_deletes=True)
    community: Mapped[Optional["Community"]] = relationship("Community", passive_deletes=True)

    __table_args__ = (
        # community, review 둘 중 하나 강제 입력
        CheckConstraint(
            "(review_id IS NOT NULL AND community_id IS NULL) OR (review_id IS NULL AND community_id IS NOT NULL)",
            name="ck_img_owner_one",
        ),

        # 리뷰 정렬 중복 방지
        UniqueConstraint("review_id", "sort_order", name="uk_review_sort"),

        # 커뮤니티 1장 강제
        UniqueConstraint("community_id", name="uk_community_one_image"),

        Index("idx_img_member_id", "member_id"),
        Index("idx_img_review_id", "review_id"),
        Index("idx_img_community_id", "community_id"),
    )