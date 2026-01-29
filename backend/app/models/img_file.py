from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, Index, text,
)
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

# owner_type은 리뷰/커뮤니티만 허용
OwnerType = Enum("REVIEW", "COMMUNITY", name="file_owner_type")


class FileUpload(Base):
    __tablename__ = "img_file"

    file_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_key: Mapped[str] = mapped_column(String(255), nullable=False)

    owner_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'review' | 'community'
    owner_id: Mapped[int] = mapped_column(Integer, nullable=False)

    member_id: Mapped[int] = mapped_column(
        ForeignKey("Member.member_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )

    created_at: Mapped[DateTime] = created_at()
    updated_at: Mapped[DateTime] = updated_at()

    __table_args__ = (
        Index("idx_img_owner", "owner_type", "owner_id"),
        Index("idx_img_member_id", "member_id"),
    )

    member: Mapped["Member"] = relationship(back_populates="img_files")