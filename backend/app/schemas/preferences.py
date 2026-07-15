from pydantic import BaseModel, field_serializer
from typing import Optional, Any
from decimal import Decimal
from uuid import UUID


class PreferencesBase(BaseModel):
    preferred_provider: Optional[str] = "deepseek"
    preferred_model: Optional[str] = "deepseek/deepseek-chat"
    temperature: Optional[Decimal] = Decimal("0.2")
    max_tokens: Optional[int] = 4096
    default_budget_limit: Optional[Decimal] = Decimal("0.10")
    daily_budget_limit: Optional[Decimal] = Decimal("1.00")
    theme: Optional[str] = "light"
    editor_font_size: Optional[int] = 14
    show_token_counts: Optional[bool] = True
    email_notifications: Optional[bool] = False
    task_completion_notifications: Optional[bool] = True


class PreferencesResponse(PreferencesBase):
    id: Any
    user_id: Any

    class Config:
        from_attributes = True

    @field_serializer("id", "user_id")
    def serialize_uuid(self, value: Any) -> str:
        if isinstance(value, UUID):
            return str(value)
        return str(value)
