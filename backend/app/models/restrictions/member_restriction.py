from sqlalchemy import (
    ForeignKey, Integer, Index, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class MemberRestrictions(Base):
    __tablename__ = "member_restrictions"

    member_restrictions_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("restriction_items.item_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    member_id: Mapped[int] = mapped_column(ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    # member_restrictions_id = Column(Integer, primary_key=True, autoincrement=True)
    # item_id = Column(Integer, ForeignKey("restriction_items.item_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    # member_id = Column(Integer, ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)


    # 관계 모델 / 테이블
    member: Mapped["Member"]  = relationship("Member", back_populates="restrictions")
    item: Mapped["Item"]  = relationship("Item", back_populates="member_restrictions")

    __table_args__ = (
        UniqueConstraint("member_id", "item_id", name="uq_member_item"),
        Index("idx_mr_item_id", "item_id"),
        Index("idx_mr_member_id", "member_id"),
    )