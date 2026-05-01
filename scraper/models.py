from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

class GroupModel(BaseModel):
    idx: int
    url: str
    last_visited: Optional[datetime] = None


class PostModel(BaseModel):
    author: str = ''
    text: str = ''
    created_at: Optional[datetime] = None
    url: str = ''
    raw_content: str = ''