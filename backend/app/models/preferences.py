from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.database import Base
import uuid


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)

    # AI Provider preferences
    preferred_provider = Column(String(50), default="deepseek")
    preferred_model = Column(String(100), default="deepseek/deepseek-chat")
    temperature = Column(Numeric(3, 2), default=0.2)
    max_tokens = Column(Integer, default=4096)

    # Budget defaults
    default_budget_limit = Column(Numeric(10, 4), default=0.10)
    daily_budget_limit = Column(Numeric(10, 4), default=1.00)

    # UI preferences
    theme = Column(String(20), default="light")
    editor_font_size = Column(Integer, default=14)
    show_token_counts = Column(Boolean, default=True)

    # Notifications
    email_notifications = Column(Boolean, default=False)
    task_completion_notifications = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
