# model 관리

from backend.app.core.database import Base

# ✅ 반드시 모델들을 import 해서 매퍼 등록되게 함
from backend.app.models.member import Member
# from backend.app.models.review import Review
# from backend.app.models.community import Community
from backend.app.models.file_upload import FileUpload