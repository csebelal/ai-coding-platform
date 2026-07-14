"""
End-to-end workflow demo script.
Demonstrates the full orchestrator pipeline working with placeholder agents.
Usage: docker compose exec backend python -m app.demo.workflow_demo
"""

import asyncio
import json
from app.services.orchestrator import orchestrator


async def run_demo():
    print("=" * 60)
    print("AI Software Engineering Platform - Workflow Demo")
    print("=" * 60)

    demo_task_id = "demo-task-001"
    demo_description = (
        "Create a Python function called `fibonacci` that takes an integer n "
        "and returns the nth Fibonacci number. Include type hints and a docstring."
    )
    demo_repository_url = "https://github.com/octocat/Hello-World"
    demo_files_changed = []
    demo_tests_results = []

    print(f"\nTask: {demo_description}")
    print(f"Repository: {demo_repository_url}")
    print("\nStarting workflow...\n")

    workflow_states = []

    async for event in orchestrator.execute(
        task_id=demo_task_id,
        description=demo_description,
        repository_url=demo_repository_url,
        files_changed=demo_files_changed,
        tests_results=demo_tests_results,
    ):
        state = event.get("state", "")
        agent = event.get("agent", "")
        detail = event.get("detail", "")

        if state == "error":
            print(f"  ERROR: {detail}")
            break

        if state == "completed":
            print(f"\n{'=' * 60}")
            print("WORKFLOW COMPLETED")
            print(f"{'=' * 60}")
            print(f"States visited: {' -> '.join(workflow_states)}")
            print(f"Final result: {json.dumps(event, indent=2, default=str)}")
            break

        if state and state not in workflow_states:
            workflow_states.append(state)

        if agent:
            print(f"  [{state}] Running agent: {agent}...")
        elif detail:
            print(f"  [{state}] {detail}")

    print("\nDemo complete!")


if __name__ == "__main__":
    asyncio.run(run_demo())
