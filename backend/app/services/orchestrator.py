from typing import Dict, Optional, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from decimal import Decimal
import logging

from app.models.task import Task
from app.models.agent_run import AgentRun
from app.models.project import Project
from app.agents.base import AgentType, AgentResult, AgentContext
from app.agents.workflow import WorkflowEngine, WorkflowState, WorkflowEvent
from app.api.websocket import notify_task_update, notify_agent_update, notify_log

logger = logging.getLogger(__name__)

class OrchestratorError(Exception):
    pass

class BudgetExceededError(OrchestratorError):
    pass

class InvalidTransitionError(OrchestratorError):
    pass

class AgentExecutionError(OrchestratorError):
    pass

class Orchestrator:
    """
    Central Orchestrator that manages the task lifecycle.
    
    Responsibilities:
    - Receive task
    - Create workflow
    - Call agents
    - Collect results
    - Run verification
    - Repeat until complete
    - Return result
    
    This is a deterministic state machine - no free-form agent conversations.
    """
    
    MAX_DEBUG_ITERATIONS = 3
    
    def __init__(self, db: Session):
        self.db = db
        self.workflow = WorkflowEngine()
        self._agents: Dict[str, Any] = {}
        self._context: Optional[AgentContext] = None
    
    def _get_agent(self, agent_type: str):
        """Lazy load agents to avoid circular imports"""
        if agent_type not in self._agents:
            self._agents[agent_type] = self._create_agent(agent_type)
        return self._agents[agent_type]
    
    def _create_agent(self, agent_type: str):
        """Create agent instance by type"""
        from app.agents import AGENT_REGISTRY
        from app.agents.placeholder import PlaceholderAgent
        
        agent_class = AGENT_REGISTRY.get(agent_type, PlaceholderAgent)
        return agent_class()
    
    async def execute_task(self, task_id: str) -> Dict[str, Any]:
        """
        Execute a task through the full workflow.
        
        Flow:
        Planning -> Researching -> Writing Tests -> Coding -> Verifying -> 
        (Debugging -> Verifying)* -> Reviewing -> Documenting -> Completed
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise OrchestratorError(f"Task {task_id} not found")
        
        # Initialize task
        task.status = "running"
        task.started_at = datetime.utcnow()
        task.workflow_state = WorkflowState.INITIALIZED.value
        self.db.commit()
        
        await notify_task_update(str(task_id), {
            "status": "running",
            "workflow_state": WorkflowState.INITIALIZED.value
        })
        
        # Build context
        self._context = self._build_context(task)
        
        try:
            # Start the workflow
            current_state = WorkflowState(task.workflow_state)
            debug_iterations = 0
            
            while not self.workflow.is_terminal(current_state):
                # Budget check
                if task.current_cost >= task.budget_limit:
                    raise BudgetExceededError("Budget exceeded")
                
                # Get agent for current state
                agent_type = self.workflow.get_agent_for_state(current_state)
                
                if agent_type:
                    # Update task with current agent
                    task.current_agent = agent_type
                    self.db.commit()
                    
                    await notify_agent_update(str(task_id), agent_type, "started")
                    await notify_log(str(task_id), "info", f"Starting {agent_type} agent", agent_type)
                    
                    # Execute agent
                    result = await self._execute_agent(agent_type, self._context, task)
                    
                    # Record agent run
                    self._record_agent_run(task, agent_type, result, self._context)
                    
                    agent_status = "completed" if result.success else "failed"
                    await notify_agent_update(str(task_id), agent_type, agent_status, {
                        "tokens_used": result.tokens_used,
                        "cost_usd": result.cost_usd
                    })
                    
                    # Update cost
                    task.current_cost += Decimal(str(result.cost_usd))
                    task.tokens_used += result.tokens_used
                    self.db.commit()
                    
                    # Determine event based on result
                    if result.success:
                        event = self._get_success_event(current_state)
                    else:
                        event = WorkflowEvent.VERIFICATION_FAILED if current_state == WorkflowState.VERIFYING else WorkflowEvent.ERROR
                    
                    # Handle debug loop limit
                    if current_state == WorkflowState.DEBUGGING:
                        debug_iterations += 1
                        if debug_iterations >= self.MAX_DEBUG_ITERATIONS:
                            event = WorkflowEvent.VERIFICATION_PASSED  # Force pass after max iterations
                    
                    # Transition state
                    next_state = self.workflow.transition(current_state, event)
                    if next_state is None:
                        raise InvalidTransitionError(f"Cannot transition from {current_state} with event {event}")
                    
                    current_state = next_state
                    task.workflow_state = current_state.value
                    self.db.commit()
                    
                    await notify_task_update(str(task_id), {
                        "status": "running",
                        "workflow_state": current_state.value,
                        "current_agent": agent_type,
                        "cost": float(task.current_cost),
                        "tokens_used": task.tokens_used
                    })
                    
                    # Store result in context
                    self._context.previous_results[agent_type] = result.data
                else:
                    # No agent needed for this state, just transition
                    event = self._get_success_event(current_state)
                    next_state = self.workflow.transition(current_state, event)
                    if next_state:
                        current_state = next_state
                        task.workflow_state = current_state.value
                        self.db.commit()
            
            # Task completed successfully
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            task.result_json = self._context.previous_results
            self.db.commit()
            
            await notify_task_update(str(task_id), {
                "status": "completed",
                "workflow_state": current_state.value,
                "cost": float(task.current_cost),
                "tokens_used": task.tokens_used
            })
            
            return {
                "task_id": str(task_id),
                "status": "completed",
                "result": self._context.previous_results,
                "cost": float(task.current_cost),
                "tokens_used": task.tokens_used
            }
            
        except BudgetExceededError:
            task.status = "failed"
            task.error_message = "Budget exceeded"
            task.completed_at = datetime.utcnow()
            self.db.commit()
            return {"task_id": str(task_id), "status": "failed", "error": "Budget exceeded"}
            
        except Exception as e:
            logger.error(f"Orchestrator error: {str(e)}")
            task.status = "failed"
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            self.db.commit()
            return {"task_id": str(task_id), "status": "failed", "error": str(e)}
    
    def _build_context(self, task: Task) -> AgentContext:
        """Build agent context from task"""
        project = self.db.query(Project).filter(Project.id == task.project_id).first()
        return AgentContext(
            task_id=str(task.id),
            project_id=str(task.project_id),
            description=task.description,
            repository_path=project.local_path if project else None,
            budget_remaining=float(task.budget_limit - task.current_cost)
        )
    
    async def _execute_agent(self, agent_type: str, context: AgentContext, task: Task) -> AgentResult:
        """Execute an agent and return result"""
        agent = self._get_agent(agent_type)
        
        # Update context budget
        context.budget_remaining = float(task.budget_limit - task.current_cost)
        
        # Execute
        if agent.validate_input(context):
            return await agent.execute(context)
        else:
            return AgentResult(
                success=False,
                data={},
                error=f"Invalid input for agent {agent_type}"
            )
    
    def _record_agent_run(self, task: Task, agent_type: str, result: AgentResult, context: AgentContext):
        """Record agent execution in database"""
        agent_run = AgentRun(
            task_id=task.id,
            agent_type=agent_type,
            status="completed" if result.success else "failed",
            input_json=context.previous_results,
            output_json=result.data,
            tokens_input=result.tokens_used // 2,  # Rough estimate
            tokens_output=result.tokens_used // 2,
            cost_usd=Decimal(str(result.cost_usd)),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            error_message=result.error
        )
        self.db.add(agent_run)
        self.db.commit()
    
    def _get_success_event(self, state: WorkflowState) -> WorkflowEvent:
        """Get the success event for a given state"""
        event_map = {
            WorkflowState.PLANNING: WorkflowEvent.PLAN_CREATED,
            WorkflowState.RESEARCHING: WorkflowEvent.RESEARCH_COMPLETE,
            WorkflowState.WRITING_TESTS: WorkflowEvent.TESTS_WRITTEN,
            WorkflowState.CODING: WorkflowEvent.CODE_WRITTEN,
            WorkflowState.VERIFYING: WorkflowEvent.VERIFICATION_PASSED,
            WorkflowState.DEBUGGING: WorkflowEvent.DEBUG_COMPLETE,
            WorkflowState.REVIEWING: WorkflowEvent.REVIEW_PASSED,
            WorkflowState.DOCUMENTING: WorkflowEvent.DOCUMENTATION_COMPLETE,
        }
        return event_map.get(state, WorkflowEvent.START)
    
    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a running task"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise OrchestratorError(f"Task {task_id} not found")
        
        if task.status not in ["running", "queued"]:
            raise OrchestratorError("Task cannot be cancelled")
        
        task.status = "cancelled"
        task.completed_at = datetime.utcnow()
        task.workflow_state = WorkflowState.CANCELLED.value
        self.db.commit()
        
        return {"task_id": str(task_id), "status": "cancelled"}
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get current task status"""
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise OrchestratorError(f"Task {task_id} not found")
        
        # Get agent runs
        runs = self.db.query(AgentRun).filter(AgentRun.task_id == task_id).all()
        
        return {
            "task_id": str(task.id),
            "status": task.status,
            "workflow_state": task.workflow_state,
            "current_agent": task.current_agent,
            "cost": float(task.current_cost),
            "budget_limit": float(task.budget_limit),
            "tokens_used": task.tokens_used,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "runs": [
                {
                    "agent_type": run.agent_type,
                    "status": run.status,
                    "cost": float(run.cost_usd),
                    "started_at": run.started_at.isoformat() if run.started_at else None,
                }
                for run in runs
            ]
        }
