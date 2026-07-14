from celery_app import celery_app
import asyncio


@celery_app.task(bind=True, name="tasks.execute_orchestrator")
def execute_orchestrator(self, task_id: str):
    """Execute the orchestrator for a given task"""
    from app.services.orchestrator import Orchestrator
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        orchestrator = Orchestrator(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(orchestrator.execute_task(task_id))
        finally:
            loop.close()
        return result
    finally:
        db.close()


@celery_app.task(bind=True, name="tasks.cancel_task")
def cancel_task(task_id: str):
    """Cancel a running task"""
    from app.services.orchestrator import Orchestrator
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        orchestrator = Orchestrator(db)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(orchestrator.cancel_task(task_id))
        finally:
            loop.close()
        return result
    finally:
        db.close()


@celery_app.task(bind=True, name="tasks.index_repository")
def index_repository(project_id: str, repo_url: str):
    """Index a repository for vector search"""
    from app.services.repository_indexer import RepositoryIndexer
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        indexer = RepositoryIndexer(db)
        result = indexer.index_repository(project_id, repo_url)
        return result
    finally:
        db.close()
