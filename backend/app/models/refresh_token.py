from sqlalchemy import (
    DateTime, ForeignKey,String, text
)
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.app.core.database import Base

# refresh 원문 저장 아닌 hash 처리된 값 저장
class RefreshToken(Base):
    __tablename__ = "refresh_token"

    # ERD: member_id가 PK,FK (1인 1토큰)
    member_id: Mapped[int] = mapped_column(ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)

    # 토큰 고유 값
    jti: Mapped[str] = mapped_column(String(255), nullable=False)
    # 토큰 해쉬 처리
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # 토큰 생성일
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    # 토큰 수정일
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 토큰 db 생성일
    create_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    # 토큰 db 수정일
    update_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"), server_onupdate=text("CURRENT_TIMESTAMP"))


    # 관계 모델 / 테이블
    member: Mapped["Member"] = relationship("Member", back_populates="refresh_token")



    # member_id = Column(Integer, ForeignKey("member.member_id", ondelete="CASCADE"), primary_key=True)
    #
    # jti = Column(String(255), nullable=False, index=True)
    # token_hash = Column(String(255), nullable=False)
    # expires_at = Column(DateTime(timezone=True), nullable=False)
    # revoked_at = Column(DateTime(timezone=True), nullable=True)
    #
    # created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    # updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    #
    # member = relationship("Member", back_populates="refresh_token")