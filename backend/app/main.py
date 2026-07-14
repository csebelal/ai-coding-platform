from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.logging_config import setup_logging
from app.error_handlers import (
    global_exception_handler,
    sqlalchemy_exception_handler,
    budget_exception_handler,
    agent_exception_handler,
    repo_exception_handler,
    InsufficientBudgetError,
    AgentExecutionError,
    RepositoryCloneError,
)
from sqlalchemy.exc import SQLAlchemyError
from app.api import health, auth, projects, tasks, repository, context, websocket, preferences, demo

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI Software Engineering Platform with multi-agent orchestration",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Exception handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
app.add_exception_handler(InsufficientBudgetError, budget_exception_handler)
app.add_exception_handler(AgentExecutionError, agent_exception_handler)
app.add_exception_handler(RepositoryCloneError, repo_exception_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(repository.router, prefix="/api/v1/repository", tags=["repository"])
app.include_router(context.router, prefix="/api/v1/context", tags=["context"])
app.include_router(websocket.router, tags=["websocket"])
app.include_router(preferences.router, prefix="/api/v1/preferences", tags=["preferences"])
app.include_router(demo.router, prefix="/api/v1/demo", tags=["demo"])

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": "0.1.0",
        "docs": "/docs"
    }
