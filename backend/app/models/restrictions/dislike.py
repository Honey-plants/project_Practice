from sqlalchemy import (
    Integer, Text, ForeignKey, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class Dislike(Base):
    __tablename__ = "restriction_dislike"

    dislike_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dislike_tag: Mapped[str] = mapped_column(Text, nullable=False)

    member_id: Mapped[int] = mapped_column(ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False)

    # dislike_id = Column(Integer, primary_key=True, autoincrement=True)
    # member_id = Column(Integer, ForeignKey("member.member_id", ondelete="CASCADE"), nullable=False, unique=True)
    # dislike_tag = Column(Text, nullable=True)

    # 관계 모델 / 테이블
    member: Mapped["Member"] = relationship("Member", back_populates="dislike")

    __table_args__ = (Index("idx_dislike_member_id", "member_id"),)
