from typing import List
from sqlalchemy import (
    Boolean, ForeignKey, String, Integer, Index, text, DateTime
)
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class Item(Base):
    __tablename__ = "restriction_items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_label_ko: Mapped[str] = mapped_column(String(50), nullable=False)
    item_label_en: Mapped[str] = mapped_column(String(50), nullable=False)
    item_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))
    category_id: Mapped[int] = mapped_column(ForeignKey("restriction_category.category_id"), nullable=False)

    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), server_onupdate=text("CURRENT_TIMESTAMP"))

    # item_id = Column(Integer, primary_key=True, autoincrement=True)
    # item_label_ko = Column(String(100), nullable=False)
    # item_label_en = Column(String(100), nullable=False)
    # item_active = Column(Boolean, nullable=False, server_default="1")
    # category_id = Column(Integer, ForeignKey("restriction_category.category_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)

    # 관계 모델 / 테이블
    category: Mapped["Category"] = relationship("Category", back_populates="item")
    member_restrictions: Mapped[List["MemberRestrictions"]] = relationship("MemberRestrictions", back_populates="item")

    # category = relationship("Category", back_populates="item")
    # member_restrictions = relationship("MemberRestrictions", back_populates="item")

    # FK 컬럼은 명시적으로 인덱스 걸어주는게 좋음.
    __table_args__ = (
        Index("idx_items_category_id", "category_id"),
    )
