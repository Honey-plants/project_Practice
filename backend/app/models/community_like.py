# from sqlalchemy import DateTime, ForeignKey, Integer, Index, text, UniqueConstraint
# from datetime import datetime
# from sqlalchemy.orm import Mapped, mapped_column
# from backend.app.core.database import Base


# class CommunityLike(Base):
#     __tablename__ = "community_like"

#     like_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

#     community_id: Mapped[int] = mapped_column(
#         ForeignKey("community.community_id", ondelete="CASCADE", onupdate="CASCADE"),
#         nullable=False,
#     )
#     member_id: Mapped[int] = mapped_column(
#         ForeignKey("member.member_id", ondelete="CASCADE", onupdate="CASCADE"),
#         nullable=False,
#     )

#     create_at: Mapped[datetime] = mapped_column(
#         DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
#     )

#     __table_args__ = (
#         UniqueConstraint("community_id", "member_id", name="uk_community_member_like"),
#         Index("idx_like_community_id", "community_id"),
#         Index("idx_like_member_id", "member_id"),
#     )
