from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    
    # Orchestration fields
    status = Column(String, default="pending", index=True)
    current_agent = Column(String, nullable=True)
    workflow_state = Column(String, default="initialized")
    workflow_data = Column(JSONB, default={})
    
    # Cost tracking
    budget_limit = Column(Numeric(10, 4), default=0.10)
    current_cost = Column(Numeric(10, 6), default=0)
    tokens_used = Column(Integer, default=0)
    
    # Results
    result_json = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
