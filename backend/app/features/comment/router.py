import uuid
import json
from typing import List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security.deps import get_current_member
# from backend.app.common.utils.debug import log_exception
from backend.app.features.community.schemas import CommunityUpdate, CommunityCreate, CommunityRead, CommunityListRead
from backend.app.features.community import service
from backend.app.models.community import Community

# comment
from backend.app.models.comment import Comment
# from backend.app.features.comment.service import
# from backend.app.features.comment.schemas import

