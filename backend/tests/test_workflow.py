import pytest
from app.agents.base import AgentType, AgentContext, ContextBudget, AgentResult
from app.agents.workflow import WorkflowEngine, WorkflowState, WorkflowEvent


def test_workflow_initial_to_planning():
    engine = WorkflowEngine()
    assert engine.get_initial_state() == WorkflowState.INITIALIZED

    next_state = engine.transition(WorkflowState.INITIALIZED, WorkflowEvent.START)
    assert next_state == WorkflowState.PLANNING


def test_workflow_planning_to_researching():
    engine = WorkflowEngine()
    next_state = engine.transition(WorkflowState.PLANNING, WorkflowEvent.PLAN_CREATED)
    assert next_state == WorkflowState.RESEARCHING


def test_workflow_full_happy_path():
    engine = WorkflowEngine()
    state = WorkflowState.INITIALIZED

    transitions = [
        (WorkflowEvent.START, WorkflowState.PLANNING),
        (WorkflowEvent.PLAN_CREATED, WorkflowState.RESEARCHING),
        (WorkflowEvent.RESEARCH_COMPLETE, WorkflowState.WRITING_TESTS),
        (WorkflowEvent.TESTS_WRITTEN, WorkflowState.CODING),
        (WorkflowEvent.CODE_WRITTEN, WorkflowState.VERIFYING),
        (WorkflowEvent.VERIFICATION_PASSED, WorkflowState.REVIEWING),
        (WorkflowEvent.REVIEW_PASSED, WorkflowState.DOCUMENTING),
        (WorkflowEvent.DOCUMENTATION_COMPLETE, WorkflowState.COMPLETED),
    ]

    for event, expected_state in transitions:
        state = engine.transition(state, event)
        assert state == expected_state, f"Expected {expected_state} after {event}"

    assert engine.is_terminal(WorkflowState.COMPLETED)


def test_workflow_debug_loop():
    engine = WorkflowEngine()

    state = engine.transition(WorkflowState.VERIFYING, WorkflowEvent.VERIFICATION_FAILED)
    assert state == WorkflowState.DEBUGGING

    state = engine.transition(WorkflowState.DEBUGGING, WorkflowEvent.DEBUG_COMPLETE)
    assert state == WorkflowState.VERIFYING


def test_workflow_invalid_transition():
    engine = WorkflowEngine()
    result = engine.transition(WorkflowState.COMPLETED, WorkflowEvent.START)
    assert result is None


def test_workflow_get_valid_events():
    engine = WorkflowEngine()
    events = engine.get_valid_events(WorkflowState.PLANNING)
    assert WorkflowEvent.PLAN_CREATED in events
    assert WorkflowEvent.ERROR in events


def test_workflow_get_agent_for_state():
    engine = WorkflowEngine()
    assert engine.get_agent_for_state(WorkflowState.PLANNING) == "planner"
    assert engine.get_agent_for_state(WorkflowState.CODING) == "coder"
    assert engine.get_agent_for_state(WorkflowState.DEBUGGING) == "debugger"
    assert engine.get_agent_for_state(WorkflowState.COMPLETED) is None


def test_context_budget():
    budget = ContextBudget(total_tokens=1000)
    assert budget.remaining == 1000

    allocated = budget.allocate(300)
    assert allocated is True
    assert budget.remaining == 700

    allocated = budget.allocate(800)
    assert allocated is False
    assert budget.remaining == 700


def test_agent_context_creation():
    context = AgentContext(
        task_id="test-task",
        project_id="test-project",
        description="Add a function"
    )
    assert context.task_id == "test-task"
    assert context.previous_results == {}
    assert context.budget_remaining == 0.10


def test_agent_result():
    result = AgentResult(
        success=True,
        data={"plan": "test"},
        tokens_used=100,
        cost_usd=0.001
    )
    assert result.success is True
    assert result.tokens_used == 100
