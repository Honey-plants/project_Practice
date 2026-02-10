from sqlalchemy import (
    DateTime, Integer, String, text
)
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

class Member(Base):
    __tablename__ = "member"

    member_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    country: Mapped[str] = mapped_column(String(20), nullable=False)
    role: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, server_default=text("USER"))

    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), server_onupdate=text("CURRENT_TIMESTAMP"))

    # member_create = Column(DateTime, nullable=False, server_default=func.now())
    # member_update = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    # created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    # updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"), server_onupdate=text("CURRENT_TIMESTAMP"))

    # member_id = Column(Integer, primary_key=True, autoincrement=True)
    # email = Column(String(255), nullable=False, unique=True)
    # password = Column(String(255), nullable=False)  # 해시 저장 전제
    # nickname = Column(String(50), nullable=False, unique=True)
    # gender = Column(String(10), nullable=False)
    # country = Column(String(50), nullable=False)
    # create_member = Column(DateTime, nullable=False, server_default=func.now())
    # modify_member = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    # role = Column(String(20), nullable=False, default="USER") # USER / ADMIN

    # restrictions = relationship("MemberRestrictions", back_populates="member", cascade="all, delete-orphan", passive_deletes=True)

    # 관계 모델 / 테이블
    restrictions: Mapped[List["MemberRestrictions"]] = relationship("MemberRestrictions", back_populates="member", passive_deletes=True)
    dislike: Mapped[List["Dislike"]] = relationship("Dislike", back_populates="member", passive_deletes=True)
    review: Mapped[List["Review"]] = relationship("Review", back_populates="member", passive_deletes=True)
    community: Mapped[List["Community"]] = relationship("Community", back_populates="member", passive_deletes=True)
    refresh_token: Mapped[Optional["RefreshToken"]] = relationship("RefreshToken", back_populates="member", uselist=False, cascade="all, delete-orphan", passive_deletes=True)
    comment: Mapped[List["Comment"]] = relationship("Comment", back_populates="member", passive_deletes=True)
    img_file = relationship("ImgFile", back_populates="member", cascade="all, delete-orphan")

    # dislike = relationship("Dislike", back_populates="member", cascade="all, delete-orphan", passive_deletes=True)
    # refresh_token = relationship("RefreshToken", uselist=False, back_populates="member", cascade="all, delete-orphan")
    # file_upload = relationship("FileUpload", back_populates="member", cascade="all, delete-orphan")
    # review = relationship("Review", back_populates="member", cascade="all, delete-orphan")
    # community = relationship("Community", back_populates="member", cascade="all, delete-orphan")