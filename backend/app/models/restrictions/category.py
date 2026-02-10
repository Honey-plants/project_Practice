from sqlalchemy import (
    Integer, String, Boolean, text, DateTime
)
from datetime import datetime
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class Category(Base):
    __tablename__ = "restriction_category"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_label_ko: Mapped[str] = mapped_column(String(50), nullable=False)
    category_label_en: Mapped[str] = mapped_column(String(50), nullable=False)
    category_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("TRUE"))

    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), server_onupdate=text("CURRENT_TIMESTAMP"))

    # category_active = Column(Boolean, nullable=False, server_default="1")

    # created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    # updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), server_onupdate=text("CURRENT_TIMESTAMP"))

    # 관계 모델 / 테이블
    item: Mapped[List["Item"]] = relationship("Item", back_populates="category")
    # item = relationship("Item", back_populates="category")