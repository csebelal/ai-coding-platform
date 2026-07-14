from pydantic import BaseModel, field_serializer
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal

class TaskBase(BaseModel):
    title: Optional[str] = None
    description: str

class TaskCreate(TaskBase):
    project_id: str
    budget_limit: Optional[Decimal] = Decimal("0.10")

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    budget_limit: Optional[Decimal] = None

class TaskResponse(TaskBase):
    id: Any
    project_id: Any
    status: str
    workflow_state: Optional[str]
    current_agent: Optional[str]
    budget_limit: Decimal
    current_cost: Decimal
    tokens_used: int
    error_message: Optional[str]
    result_json: Optional[dict]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    @field_serializer('id', 'project_id')
    def serialize_uuid(self, value, _info):
        return str(value)

    class Config:
        from_attributes = True

class AgentRunResponse(BaseModel):
    id: Any
    task_id: Any
    agent_type: str
    status: str
    model_used: Optional[str]
    tokens_input: int
    tokens_output: int
    cost_usd: Decimal
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    created_at: datetime

    @field_serializer('id', 'task_id')
    def serialize_uuid(self, value, _info):
        return str(value)

    class Config:
        from_attributes = True
