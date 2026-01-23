from fastapi import APIRouter

from backend.app.features.member.router import router as member_router
from backend.app.features.auth.router import router as auth_router
from backend.app.features.debug.router import router as debug_router
from backend.app.features.restrictions.router import router as restrictions_router
from backend.app.features.restrictions.admin_router import router as restrictions_admin
from backend.app.features.recipe.router import router as recipe_router

# from backend.app.features.images.router import router as receipt_router
# router 미작업
# from .features.review.router import router as review_router
# from .features.community.router import router as community_router

# router 전체 관리
api_router = APIRouter()

api_router.include_router(member_router)
api_router.include_router(auth_router)
api_router.include_router(debug_router)
api_router.include_router(restrictions_router)
api_router.include_router(restrictions_admin)
api_router.include_router(recipe_router)

# 임시 menu img upload 테스트 router
# api_router.include_router(menu_router)


# router 미작업
# api_router.include_router(review_router)
# api_router.include_router(community_router)

