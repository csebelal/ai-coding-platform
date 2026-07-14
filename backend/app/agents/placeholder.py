from typing import Dict, Any
from app.agents.base import BaseAgent, AgentType, AgentResult, AgentContext

class PlaceholderAgent(BaseAgent):
    """Placeholder agent for testing orchestrator flow"""
    
    def __init__(self, agent_type: str = "placeholder"):
        self.agent_type = agent_type
    
    def validate_input(self, context: AgentContext) -> bool:
        return True
    
    async def execute(self, context: AgentContext) -> AgentResult:
        """Placeholder execution - will be replaced by real agents in Sprint 6"""
        return AgentResult(
            success=True,
            data={
                "agent_type": self.agent_type,
                "task_id": context.task_id,
                "message": f"Placeholder {self.agent_type} executed successfully"
            },
            tokens_used=0,
            cost_usd=0.0
        )
