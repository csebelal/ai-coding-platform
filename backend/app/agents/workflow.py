from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

class WorkflowState(str, Enum):
    """States in the task workflow"""
    INITIALIZED = "initialized"
    QUEUED = "queued"
    PLANNING = "planning"
    RESEARCHING = "researching"
    WRITING_TESTS = "writing_tests"
    CODING = "coding"
    VERIFYING = "verifying"
    DEBUGGING = "debugging"
    REVIEWING = "reviewing"
    DOCUMENTING = "documenting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WorkflowEvent(str, Enum):
    """Events that trigger state transitions"""
    START = "start"
    PLAN_CREATED = "plan_created"
    RESEARCH_NEEDED = "research_needed"
    RESEARCH_COMPLETE = "research_complete"
    TESTS_WRITTEN = "tests_written"
    CODE_WRITTEN = "code_written"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED = "verification_failed"
    DEBUG_COMPLETE = "debug_complete"
    REVIEW_PASSED = "review_passed"
    REVIEW_FAILED = "review_failed"
    DOCUMENTATION_COMPLETE = "documentation_complete"
    ERROR = "error"
    CANCEL = "cancel"

@dataclass
class Transition:
    from_state: WorkflowState
    event: WorkflowEvent
    to_state: WorkflowState
    agent_type: Optional[str] = None
    conditions: List[str] = field(default_factory=list)

class WorkflowEngine:
    """Deterministic state machine for task orchestration"""
    
    def __init__(self):
        self.transitions = self._build_transitions()
        self.state_agents = self._build_state_agents()
    
    def _build_transitions(self) -> List[Transition]:
        """Define all valid state transitions"""
        return [
            # Initialization
            Transition(WorkflowState.INITIALIZED, WorkflowEvent.START, WorkflowState.PLANNING),
            
            # Planning
            Transition(WorkflowState.PLANNING, WorkflowEvent.PLAN_CREATED, WorkflowState.RESEARCHING),
            Transition(WorkflowState.PLANNING, WorkflowEvent.ERROR, WorkflowState.FAILED),
            
            # Research
            Transition(WorkflowState.RESEARCHING, WorkflowEvent.RESEARCH_COMPLETE, WorkflowState.WRITING_TESTS),
            Transition(WorkflowState.RESEARCHING, WorkflowEvent.RESEARCH_NEEDED, WorkflowState.RESEARCHING),
            
            # Test Writing
            Transition(WorkflowState.WRITING_TESTS, WorkflowEvent.TESTS_WRITTEN, WorkflowState.CODING),
            
            # Coding
            Transition(WorkflowState.CODING, WorkflowEvent.CODE_WRITTEN, WorkflowState.VERIFYING),
            
            # Verification
            Transition(WorkflowState.VERIFYING, WorkflowEvent.VERIFICATION_PASSED, WorkflowState.REVIEWING),
            Transition(WorkflowState.VERIFYING, WorkflowEvent.VERIFICATION_FAILED, WorkflowState.DEBUGGING),
            
            # Debugging
            Transition(WorkflowState.DEBUGGING, WorkflowEvent.DEBUG_COMPLETE, WorkflowState.VERIFYING),
            Transition(WorkflowState.DEBUGGING, WorkflowEvent.ERROR, WorkflowState.FAILED),
            
            # Review
            Transition(WorkflowState.REVIEWING, WorkflowEvent.REVIEW_PASSED, WorkflowState.DOCUMENTING),
            Transition(WorkflowState.REVIEWING, WorkflowEvent.REVIEW_FAILED, WorkflowState.DEBUGGING),
            
            # Documentation
            Transition(WorkflowState.DOCUMENTING, WorkflowEvent.DOCUMENTATION_COMPLETE, WorkflowState.COMPLETED),
            
            # Terminal states
            Transition(WorkflowState.COMPLETED, WorkflowEvent.CANCEL, WorkflowState.CANCELLED),
            Transition(WorkflowState.FAILED, WorkflowEvent.CANCEL, WorkflowState.CANCELLED),
        ]
    
    def _build_state_agents(self) -> Dict[WorkflowState, str]:
        """Map states to their required agent types"""
        return {
            WorkflowState.PLANNING: "planner",
            WorkflowState.RESEARCHING: "researcher",
            WorkflowState.WRITING_TESTS: "test_writer",
            WorkflowState.CODING: "coder",
            WorkflowState.VERIFYING: "verifier",
            WorkflowState.DEBUGGING: "debugger",
            WorkflowState.REVIEWING: "critic",
            WorkflowState.DOCUMENTING: "doc_writer",
        }
    
    def get_valid_events(self, current_state: WorkflowState) -> List[WorkflowEvent]:
        """Get all valid events for the current state"""
        return [t.event for t in self.transitions if t.from_state == current_state]
    
    def can_transition(self, current_state: WorkflowState, event: WorkflowEvent) -> bool:
        """Check if a transition is valid"""
        return any(
            t.from_state == current_state and t.event == event 
            for t in self.transitions
        )
    
    def transition(self, current_state: WorkflowState, event: WorkflowEvent) -> Optional[WorkflowState]:
        """Execute a state transition"""
        for t in self.transitions:
            if t.from_state == current_state and t.event == event:
                return t.to_state
        return None
    
    def get_agent_for_state(self, state: WorkflowState) -> Optional[str]:
        """Get the agent type required for a state"""
        return self.state_agents.get(state)
    
    def get_initial_state(self) -> WorkflowState:
        return WorkflowState.INITIALIZED
    
    def get_terminal_states(self) -> List[WorkflowState]:
        return [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]
    
    def is_terminal(self, state: WorkflowState) -> bool:
        return state in self.get_terminal_states()
