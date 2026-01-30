from pydantic import BaseModel
from typing import Any, Dict

class MenuAnalyzeResponse(BaseModel):
    ok: bool = True
    result: Dict[str, Any]
