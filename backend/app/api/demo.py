"""
Quick demo endpoint to test the orchestrator without real AI calls.
Returns mock agent outputs for each workflow state.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/demo/workflow")
async def run_demo_workflow(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    steps = [
        {"state": "INITIALIZED", "detail": "Task initialized", "agent": None},
        {"state": "PLANNING", "detail": "Analyzing requirements", "agent": "planner"},
        {"state": "PLANNING", "detail": "Plan created: 2 functions, 1 test file", "agent": None},
        {"state": "RESEARCHING", "detail": "Searching codebase", "agent": "researcher"},
        {"state": "RESEARCHING", "detail": "Found 3 relevant files", "agent": None},
        {"state": "WRITING_TESTS", "detail": "Writing test cases", "agent": "test_writer"},
        {"state": "WRITING_TESTS", "detail": "3 test cases written", "agent": None},
        {"state": "CODING", "detail": "Implementing solution", "agent": "coder"},
        {"state": "CODING", "detail": "Implementation complete", "agent": None},
        {"state": "VERIFYING", "detail": "Running tests", "agent": None},
        {"state": "VERIFYING", "detail": "Tests passed (3/3)", "agent": None},
        {"state": "REVIEWING", "detail": "Code review", "agent": "critic"},
        {"state": "REVIEWING", "detail": "Review passed", "agent": None},
        {"state": "DOCUMENTING", "detail": "Writing documentation", "agent": "doc_writer"},
        {"state": "DOCUMENTING", "detail": "Documentation complete", "agent": None},
        {"state": "COMPLETED", "detail": "Workflow finished", "agent": None},
    ]

    return {
        "status": "demo",
        "message": "This is a demo workflow - no actual AI calls were made",
        "steps": steps,
        "total_cost_usd": 0.0042,
        "total_tokens": 2847,
    }
