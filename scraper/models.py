from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

class GroupModel(BaseModel):
    url: str
    last_visited: Optional[datetime] = None


class PostModel(BaseModel):
    author: str = ''
    text: str = ''
    created_at: Optional[datetime] = None
    url: str = ''