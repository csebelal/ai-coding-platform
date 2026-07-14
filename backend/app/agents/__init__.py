from app.agents.base import BaseAgent, AgentType, AgentResult, AgentContext, ContextBudget
from app.agents.workflow import WorkflowEngine, WorkflowState, WorkflowEvent
from app.agents.planner import PlannerAgent
from app.agents.coder import CoderAgent
from app.agents.test_writer import TestWriterAgent
from app.agents.critic import CriticAgent
from app.agents.debugger import DebuggerAgent
from app.agents.doc_writer import DocWriterAgent
from app.agents.researcher import ResearcherAgent
from app.agents.placeholder import PlaceholderAgent

AGENT_REGISTRY = {
    "planner": PlannerAgent,
    "coder": CoderAgent,
    "test_writer": TestWriterAgent,
    "critic": CriticAgent,
    "debugger": DebuggerAgent,
    "doc_writer": DocWriterAgent,
    "researcher": ResearcherAgent,
}

__all__ = [
    "BaseAgent",
    "AgentType",
    "AgentResult",
    "AgentContext",
    "ContextBudget",
    "WorkflowEngine",
    "WorkflowState",
    "WorkflowEvent",
    "PlannerAgent",
    "CoderAgent",
    "TestWriterAgent",
    "CriticAgent",
    "DebuggerAgent",
    "DocWriterAgent",
    "ResearcherAgent",
    "PlaceholderAgent",
    "AGENT_REGISTRY",
]
