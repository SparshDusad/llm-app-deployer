from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any

class Attachment(BaseModel):
    name: str
    url: str

class TaskRequest(BaseModel):
    email: str
    secret: str
    task: str
    round: int
    nonce: str
    brief: str
    checks: List[str]
    evaluation_url: HttpUrl
    attachments: Optional[List[Attachment]] = []

class APIResponse(BaseModel):
    status: str
    message: str
