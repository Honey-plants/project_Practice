# model 관리

from backend.app.core.database import Base

#  반드시 모델들을 import 해서 매퍼 등록되게 함
from backend.app.models.comment import Comment
from backend.app.models.community import Community
from backend.app.models.community_like import CommunityLike
from backend.app.models.img_file import ImgFile
from backend.app.models.member import Member
from backend.app.models.refresh_token import RefreshToken
from backend.app.models.review import Review

from backend.app.models.restrictions.category import Category
from backend.app.models.restrictions.dislike import Dislike
from backend.app.models.restrictions.item import Item
from backend.app.models.restrictions.member_restriction import MemberRestrictions