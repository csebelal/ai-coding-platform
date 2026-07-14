from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum

class AgentType(str, Enum):
    PLANNER = "planner"
    CODER = "coder"
    DEBUGGER = "debugger"
    CRITIC = "critic"
    TEST_WRITER = "test_writer"
    RESEARCHER = "researcher"
    DOC_WRITER = "doc_writer"

@dataclass
class AgentResult:
    success: bool
    data: Dict[str, Any]
    tokens_used: int = 0
    cost_usd: float = 0.0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ContextBudget:
    total_tokens: int = 8000
    used_tokens: int = 0

    @property
    def remaining(self) -> int:
        return max(0, self.total_tokens - self.used_tokens)

    def allocate(self, tokens: int) -> bool:
        if tokens <= self.remaining:
            self.used_tokens += tokens
            return True
        return False

@dataclass
class AgentContext:
    task_id: str
    project_id: str
    description: str
    repository_path: Optional[str] = None
    repository_card: Optional[Dict[str, Any]] = None
    relevant_files: List[Dict[str, Any]] = field(default_factory=list)
    relevant_symbols: List[Dict[str, Any]] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    previous_results: Dict[str, Any] = field(default_factory=dict)
    budget_remaining: float = 0.10
    token_budget: ContextBudget = field(default_factory=ContextBudget)
    metadata: Dict[str, Any] = field(default_factory=dict)

class BaseAgent(ABC):
    """Base class for all AI agents in the system"""
    
    agent_type: AgentType
    
    @abstractmethod
    async def execute(self, context: AgentContext) -> AgentResult:
        """Execute the agent's task"""
        pass
    
    @abstractmethod
    def validate_input(self, context: AgentContext) -> bool:
        """Validate that the input context is valid for this agent"""
        pass
    
    def can_execute(self, context: AgentContext) -> bool:
        """Check if this agent can execute given the context"""
        return context.budget_remaining > 0
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent"""
        return ""
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, model: str) -> float:
        """Estimate the cost of a completion"""
        # Default cost estimation - override in subclasses
        return 0.0
