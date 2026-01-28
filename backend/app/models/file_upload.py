from sqlalchemy import (
    Column, BigInteger, Integer, String, DateTime, Enum, ForeignKey, func
)
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


# owner_type은 리뷰/커뮤니티만 허용 (MENU는 DB 저장 안 함)
OwnerType = Enum("REVIEW", "COMMUNITY", name="file_owner_type")


class FileUpload(Base):
    __tablename__ = "file_upload"

    file_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 업로더(정리/권한 체크용)
    member_id = Column(Integer, ForeignKey("member.member_id", ondelete="CASCADE"), nullable=False, index=True,)

    # 어떤 게시글에 붙는지 (폴리모픽)
    owner_type = Column(OwnerType, nullable=False, index=True)  # REVIEW / COMMUNITY
    owner_id = Column(BigInteger, nullable=False, index=True)   # review_id or community_id

    # 파일 식별/저장 정보
    file_key = Column(String(36), nullable=False, unique=True)      # UUID
    org_file_name = Column(String(255), nullable=False)             # 원본명
    stored_file_name = Column(String(255), nullable=False)          # uuid.ext
    storage_path = Column(String(500), nullable=False)              # 로컬경로 or S3 key

    # 메타
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(BigInteger, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    member = relationship("Member", back_populates="file_upload")