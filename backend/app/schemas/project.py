from pydantic import BaseModel, field_serializer
from typing import Optional, Any
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    repo_url: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    repo_url: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: Any
    user_id: Any
    repo_url: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    @field_serializer('id', 'user_id')
    def serialize_uuid(self, value, _info):
        return str(value)

    class Config:
        from_attributes = True
