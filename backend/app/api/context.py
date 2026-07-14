from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.services.auth import get_current_user
from app.services.context_manager import context_manager

router = APIRouter()

class ContextBuildRequest(BaseModel):
    task_id: str
    project_id: str
    description: str
    agent_type: str
    token_budget: int = 8000

class ContextResponse(BaseModel):
    task_id: str
    project_id: str
    repository_card: Optional[dict]
    relevant_files: List[dict]
    relevant_symbols: List[dict]
    token_usage: dict

class ConversationEntryRequest(BaseModel):
    content: str
    entry_type: str
    metadata: Optional[dict] = None

@router.post("/build", response_model=ContextResponse)
async def build_context(
    request: ContextBuildRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Build context for an agent"""
    # Verify project access
    project = db.query(Project).filter(
        Project.id == request.project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify task access
    task = db.query(Task).filter(
        Task.id == request.task_id,
        Task.project_id == request.project_id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    try:
        context = await context_manager.build_context(
            task_id=request.task_id,
            project_id=request.project_id,
            description=request.description,
            agent_type=request.agent_type,
            token_budget=request.token_budget
        )
        
        return ContextResponse(
            task_id=context.task_id,
            project_id=context.project_id,
            repository_card=context.repository_card,
            relevant_files=context.relevant_files,
            relevant_symbols=context.relevant_symbols,
            token_usage={
                "total": context.token_budget.total_tokens,
                "used": context.token_budget.used_tokens,
                "remaining": context.token_budget.remaining
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to build context: {str(e)}"
        )

@router.get("/{task_id}")
async def get_context(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get cached context for a task"""
    context = context_manager.get_cached_context(task_id)
    
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Context not found"
        )
    
    return {
        "task_id": context.task_id,
        "project_id": context.project_id,
        "repository_card": context.repository_card,
        "relevant_files": context.relevant_files,
        "relevant_symbols": context.relevant_symbols,
        "token_usage": {
            "total": context.token_budget.total_tokens,
            "used": context.token_budget.used_tokens,
            "remaining": context.token_budget.remaining
        }
    }

@router.post("/conversation")
async def add_conversation_entry(
    request: ConversationEntryRequest,
    current_user: User = Depends(get_current_user)
):
    """Add entry to conversation memory"""
    from app.memory import conversation_memory
    
    entry = conversation_memory.add_entry(
        content=request.content,
        entry_type=request.entry_type,
        metadata=request.metadata
    )
    
    return {
        "id": entry.id,
        "content": entry.content,
        "entry_type": entry.entry_type,
        "timestamp": entry.timestamp.isoformat()
    }

@router.get("/conversation/history")
async def get_conversation_history(
    count: int = 10,
    entry_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get conversation history"""
    from app.memory import conversation_memory
    
    entries = conversation_memory.get_recent(count, entry_type)
    return [e.to_dict() for e in entries]

@router.delete("/{task_id}")
async def clear_context(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Clear cached context for a task"""
    context_manager.clear_cache(task_id)
    return {"message": "Context cleared"}
