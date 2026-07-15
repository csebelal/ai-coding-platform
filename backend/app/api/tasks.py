from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from celery import Celery
import os

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.agent_run import AgentRun
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, AgentRunResponse
from app.services.auth import get_current_user
from app.services.orchestrator import Orchestrator

celery_app = Celery(
    "backend",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
)

router = APIRouter()

class TaskExecuteRequest(BaseModel):
    task_id: str

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    workflow_state: Optional[str]
    current_agent: Optional[str]
    cost: float
    budget_limit: float
    tokens_used: int
    started_at: Optional[str]
    completed_at: Optional[str]
    runs: List[dict]

@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    project_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Task).join(Project).filter(Project.user_id == current_user.id)
    
    if project_id:
        query = query.filter(Task.project_id == project_id)
    
    tasks = query.all()
    return tasks

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(
        Project.id == task_data.project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    task = Task(
        project_id=task_data.project_id,
        title=task_data.title,
        description=task_data.description,
        budget_limit=task_data.budget_limit
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a running task"
        )
    
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.status is not None:
        task.status = task_data.status
    if task_data.budget_limit is not None:
        task.budget_limit = task_data.budget_limit
    
    db.commit()
    db.refresh(task)
    return task

@router.post("/{task_id}/execute")
async def execute_task(
    task_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a task using the orchestrator"""
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status not in ["pending", "failed", "completed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task is already being processed"
        )
    
    # Queue task for execution via Celery
    celery_app.send_task("tasks.execute_orchestrator", args=[str(task_id)])
    
    # Update status
    task.status = "queued"
    db.commit()
    
    return {
        "task_id": str(task.id),
        "status": "queued",
        "message": "Task queued for execution"
    }

@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a running task"""
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status not in ["running", "queued"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task cannot be cancelled"
        )
    
    # Queue cancellation via Celery
    celery_app.send_task("tasks.cancel_task", args=[str(task_id)])
    
    return {
        "task_id": str(task.id),
        "status": "cancelling",
        "message": "Task cancellation queued"
    }

@router.get("/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed task status including orchestrator state"""
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Get agent runs
    runs = db.query(AgentRun).filter(AgentRun.task_id == task_id).all()
    
    return TaskStatusResponse(
        task_id=str(task.id),
        status=task.status,
        workflow_state=task.workflow_state,
        current_agent=task.current_agent,
        cost=float(task.current_cost),
        budget_limit=float(task.budget_limit),
        tokens_used=task.tokens_used,
        started_at=task.started_at.isoformat() if task.started_at else None,
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        runs=[
            {
                "agent_type": run.agent_type,
                "status": run.status,
                "cost": float(run.cost_usd),
                "started_at": run.started_at.isoformat() if run.started_at else None,
            }
            for run in runs
        ]
    )

@router.get("/{task_id}/runs", response_model=List[AgentRunResponse])
async def get_task_runs(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(Task).join(Project).filter(
        Task.id == task_id,
        Project.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    runs = db.query(AgentRun).filter(AgentRun.task_id == task_id).all()
    return runs
